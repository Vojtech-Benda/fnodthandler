from typing import Callable, Any
from pathlib import Path
import importlib.util

from src.utils import read_env


INTERNAL_PROCESSES = {
    'dcm2other': './src/algorithms/dcm2other.py'
}


class ProcessDispatcher():
    def __init__(self):
        self.processes: dict[str, Callable[..., Any]] = {}
        
    def register_processes(self):
        print("importing internal processes")
        for process, path in INTERNAL_PROCESSES.items():
            module_name, module = self.import_method(process, Path(path))
            self.processes[process] = getattr(module, module_name)
            print(f"imported internal {process} function")
            
        print("importing external processes")
        process_paths = read_env("algorithms")
        for process, paths in process_paths.items():
                        
            if not all([paths.values()]):
                print(f"external process '{process}' missing executable/script path")
                continue
                        
            exec_path = Path(paths['exec_path']).expanduser() 
            script_path = Path(paths['script_path']).expanduser()
            func_path = Path(paths['func_path'])
            
            if not exec_path.is_file():
                print(f"external process '{process}' executable path not found/not file '{exec_path}'")
                continue
            
            if not script_path.is_file():
                print(f"external process '{process}' script path not found/not file '{script_path}'")
                continue
              
            # self.processes[process] = {'exec_path': exec_path, 'script_path': script_path}
                        
            module_name, module = self.import_method(process, func_path)
            
            self.processes[process] = getattr(module, module_name)
            print(f"registered external {process} function")
        print(f"registered processes: {", ".join(self.processes.keys())}")
    
    def import_method(self, process: str, func_path: Path):
        module_name = func_path.stem
        try:
            spec = importlib.util.spec_from_file_location(module_name, func_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        except RuntimeError as err:
            print(err)
            return None, None
        return module_name, module

    # def run_process(self, process_name: str, input_paths: list[str], output_dir: str, options: dict[str, Any] = {}):
    #     if process_name not in self.processes:
    #         raise KeyError(f"process '{process_name}' not registered")
        
    #     exec_path = self.processes[process_name]['exec_path']
    #     script_path = self.processes[process_name]['script_path']
    #     cmd = [str(exec_path), str(script_path),
    #            ]

    def get_process(self, process_name: str) -> Callable[..., Any]:
        try:
            if process_name not in self.processes:
                raise KeyError(f"external process {process_name} not registered")
            return self.processes[process_name]
        except KeyError as e:
            print(e)
        
        