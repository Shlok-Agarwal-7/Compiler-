import shutil
import subprocess
import uuid
from pathlib import Path


def normalize_output(text):
    return text.replace("\r\n", "\n").strip()


# A dedicated temporary directory for all execution-related files
TEMP_EXEC_DIR = Path("/tmp/online_judge/")


def set_limits(memory_limit_mb):
    """Sets memory limits for the child process."""
    try:
        import resource

        memory_bytes = memory_limit_mb * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
        resource.setrlimit(resource.RLIMIT_DATA, (memory_bytes, memory_bytes))
    except (ImportError, ValueError):
        pass


def compile_code(language, code_path, u_id):
    """Compiles the code and returns the path to the executable or errors."""
    compiled_dir = TEMP_EXEC_DIR / "compiled"
    compiled_dir.mkdir(parents=True, exist_ok=True)

    if language == "cpp":
        exec_path = compiled_dir / f"{u_id}.out"
        compile_cmd = ["g++", str(code_path), "-o", str(exec_path)]
        try:
            result = subprocess.run(
                compile_cmd, capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                return None, "Compilation Error: " + result.stderr
            return exec_path, None
        except subprocess.TimeoutExpired:
            return None, "Compilation Error: Timeout"

    elif language == "java":
        # For Java, the "executable" is the class name, and we need the directory path
        return code_path, None
        # class_dir = code_path.parent
        # compile_cmd = ["javac", str(code_path)]
        # try:
        #     result = subprocess.run(
        #         compile_cmd, capture_output=True, text=True, timeout=10
        #     )
        #     if result.returncode != 0:
        #         return None, "Compilation Error: " + result.stderr
        #     # Return the directory containing the .class file
        #     return class_dir, None
        # except subprocess.TimeoutExpired:
        #     return None, "Compilation Error: Timeout"

    elif language == "py":
        # Python is interpreted, no compilation needed
        return code_path, None

    return None, "Unsupported language"


def execute_code(language, exec_path, u_id, input_data, time_limit, memory_limit):
    """Executes the code/compiled executable and returns the output."""
    input_dir = TEMP_EXEC_DIR / "input"
    output_dir = TEMP_EXEC_DIR / "output"
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    input_file_path = input_dir / f"{u_id}.txt"
    output_file_path = output_dir / f"{u_id}.txt"
    input_file_path.write_text(input_data)
    output_file_path.touch()

    run_cmd = []
    if language == "cpp":
        run_cmd = [str(exec_path)]
    elif language == "py":
        run_cmd = ["python", str(exec_path)]
    elif language == "java":
        # class_name = f"{u_id}"
        run_cmd = [
            "java",
            "-Xms256m",
            "-Xmx256m",
            str(exec_path),
        ]

    try:
        with open(input_file_path, "r") as input_f, open(
            output_file_path, "w"
        ) as output_f:
            result = subprocess.run(
                run_cmd,
                stdin=input_f,
                stdout=output_f,
                stderr=subprocess.STDOUT,
                preexec_fn=lambda: set_limits(memory_limit),
                timeout=time_limit,
                text=True,
            )

        output_data = output_file_path.read_text()

        if result.returncode != 0:
            if "MemoryError" in output_data or result.returncode in [-9, 137]:
                return "Memory Limit Exceeded"
            print(output_data)
            return "RunTime Error: " + output_data

        return output_data

    except subprocess.TimeoutExpired:
        return "Time Limit Exceeded"
    except Exception as e:
        print(str(e))
        return "RunTime Error: " + str(e)
    finally:
        # Clean up input/output files for the current run
        input_file_path.unlink(missing_ok=True)
        output_file_path.unlink(missing_ok=True)


def run_code(language, code, input_data, time_limit=5, memory_limit=128):
    """Orchestrates a single run of code with custom input."""
    u_id = str(uuid.uuid4())
    code_dir = TEMP_EXEC_DIR / "code"
    code_dir.mkdir(parents=True, exist_ok=True)
    code_file_path = code_dir / f"{u_id}.{language}"
    code_file_path.write_text(code)

    exec_path, error = compile_code(language, code_file_path, u_id)

    if error:
        # Cleanup and return compilation error
        shutil.rmtree(code_dir, ignore_errors=True)
        return error

    output = execute_code(
        language, exec_path, u_id, input_data, time_limit, memory_limit
    )

    # Final cleanup
    if language in ["cpp"]:
        compiled_dir = TEMP_EXEC_DIR / "compiled"
        shutil.rmtree(compiled_dir, ignore_errors=True)
        # if language == "java":
        #     # remove .class file
        #      (code_dir / f"{u_id}.class").unlink(missing_ok=True)

    code_file_path.unlink(missing_ok=True)

    return output

def submit_code(language, code,testcases,time_limit,memory_limit):
    """Orchestrates a submission against all testcases."""
    u_id = str(uuid.uuid4())

    code_dir = TEMP_EXEC_DIR / "code"
    code_dir.mkdir(parents=True, exist_ok=True)
    code_file_path = code_dir / f"{u_id}.{language}"
    code_file_path.write_text(code)

    # 1. Compile the code once
    exec_path, compile_error = compile_code(language, code_file_path, u_id)
    if compile_error:
        code_file_path.unlink(missing_ok=True)
        return {"verdict": compile_error}

    # 2. Run against all testcases
    verdict = "Accepted"
    for i, testcase in enumerate(testcases, 1):
        print(testcase)
        output = execute_code(
            language,
            exec_path,
            u_id,
            testcase["input"],
            time_limit,
            memory_limit,
        )

        if normalize_output(output) != normalize_output(testcase["output"]):
            if "Time Limit Exceeded" in output:
                verdict = f"TLE on Testcase {i}"
            elif "Memory Limit Exceeded" in output:
                verdict = f"MLE on Testcase {i}"
            elif "RunTime Error" in output:
                print(output)
                verdict = f"Runtime Error on Testcase {i}"
            else:
                verdict = f"WA on Testcase {i}"
            break  # Stop on first failure

    # 3. Final Cleanup
    code_file_path.unlink(missing_ok=True)
    if language == "cpp":
        exec_path.unlink(missing_ok=True)
    # elif language == "java":
    #     # exec_path is a directory, and the .class file is inside it
    #     class_file = exec_path / f"{u_id}.class"
    #     class_file.unlink(missing_ok=True)

    return {"verdict": verdict}