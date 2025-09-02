from flask import Flask, request, jsonify
import subprocess
import tempfile
import json
import os
import re

app = Flask(__name__)


def validate_script(script):
    if not script or not isinstance(script, str):
        return "Script must be a non-empty string"
    
    if len(script) > 10000: 
        return "Script too large (max 10KB)"
    
    if not re.search(r'def\s+main\s*\(', script):
        return "Script must contain a main() function"
    
    dangerous_patterns = [
        r'import\s+subprocess',
        r'from\s+subprocess',
        r'import\s+socket',
        r'from\s+socket',
        r'import\s+urllib',
        r'from\s+urllib',
        r'import\s+requests',
        r'from\s+requests',
        r'__import__',
        r'eval\s*\(',
        r'exec\s*\(',
        r'open\s*\(',
        r'file\s*\(',
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, script, re.IGNORECASE):
            return f"Script contains potentially dangerous code: {pattern}"
    
    return None


@app.route('/execute', methods=['POST'])
def execute_script():

    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 400
    
    data = request.get_json(force=True)

    if not data or 'script' not in data:
        return jsonify({'error': 'Request body must contain a "script" field'}), 400

    script = data['script']
    
    validation_error = validate_script(script)
    if validation_error:
        return jsonify({'error': validation_error}), 400

    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(script)
            f.write('\n\nimport json\n')
            f.write('result = main()\n')
            f.write('print("RESULT:" + json.dumps(result))\n')
            script_path = f.name

        jail_script_path = f'/tmp/script_{os.path.basename(script_path)}'
        import shutil
        shutil.copy2(script_path, jail_script_path)

        cmd = [
            'nsjail',
            '--mode', 'o',
            '--time_limit', '30',
            '--chroot', '/',
            '--cwd', '/tmp',
            '--disable_clone_newuser',
            '--disable_clone_newnet', 
            '--disable_clone_newpid',
            '--disable_clone_newipc',
            '--disable_clone_newuts',
            '--disable_clone_newcgroup',
            '--disable_clone_newns',
            '--rlimit_cpu', '30',
            '--rlimit_as', '512',
            '--rlimit_fsize', '10',
            '--rlimit_nofile', '64',
            '--',
            '/usr/local/bin/python3', jail_script_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=35)

        os.unlink(script_path)
        os.unlink(jail_script_path)

        if result.returncode != 0:
            return jsonify({
                'error': f'nsjail failed: return code {result.returncode}',
                'stderr': result.stderr,
                'stdout': result.stdout
            }), 400

        stdout_lines = result.stdout.strip().split('\n')
        main_result = None
        stdout_output = []

        for line in stdout_lines:
            if line.startswith('RESULT:'):
                try:
                    main_result = json.loads(line[7:])
                except:
                    return jsonify({'error': 'main() must return valid JSON'}), 400
            else:
                stdout_output.append(line)

        if main_result is None:
            return jsonify({'error': 'main() function did not return a result'}), 400

        return jsonify({
            'result': main_result,
            'stdout': '\n'.join(stdout_output)
        })

    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Script execution timed out'}), 400
    except Exception as e:
        return jsonify({'error': f'Execution error: {str(e)}'}), 500


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)