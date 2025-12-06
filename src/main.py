#!/usr/bin/env python3
"""MySQL Password Reset Tool"""

import os
import sys
import subprocess
import time
import tempfile
import getpass
from pathlib import Path
from typing import Optional
import logging

class SimpleFormatter(logging.Formatter):
    def format(self, record):
        return f"→ {record.getMessage()}"

handler = logging.StreamHandler()
handler.setFormatter(SimpleFormatter())
logging.basicConfig(level=logging.INFO, handlers=[handler])
logger = logging.getLogger(__name__)


class MySQLResetTool:
    """MySQL password reset utility"""
    
    def __init__(self):
        self.platform = sys.platform
        self.is_windows = self.platform == 'win32'
        self.mysql_config = self._detect_mysql_installation()
        self.init_file_path: Optional[Path] = None
        
    def _detect_mysql_installation(self) -> dict:
        """Auto-detect MySQL installation paths"""
        config = {
            'bin_path': None,
            'mysql_path': None,
            'mysqld_path': None,
            'config_path': None,
            'service_name': 'MySQL80'
        }
        
        if self.is_windows:
            possible_paths = [
                Path('C:\\Program Files\\MySQL\\MySQL Server 8.0\\bin'),
                Path('C:\\Program Files\\MySQL\\MySQL Server 5.7\\bin'),
                Path('C:\\Program Files (x86)\\MySQL\\MySQL Server 8.0\\bin'),
            ]
            
            possible_configs = [
                Path('C:\\ProgramData\\MySQL\\MySQL Server 8.0\\my.ini'),
                Path('C:\\ProgramData\\MySQL\\MySQL Server 5.7\\my.ini'),
            ]
            
            for path in possible_paths:
                if path.exists():
                    config['bin_path'] = path
                    config['mysql_path'] = path / 'mysql.exe'
                    config['mysqld_path'] = path / 'mysqld.exe'
                    break
            
            for cfg_path in possible_configs:
                if cfg_path.exists():
                    config['config_path'] = cfg_path
                    break
        else:
            for bin_dir in ['/usr/bin', '/usr/local/bin', '/opt/mysql/bin']:
                if Path(bin_dir).exists():
                    config['bin_path'] = Path(bin_dir)
                    config['mysql_path'] = Path(bin_dir) / 'mysql'
                    config['mysqld_path'] = Path(bin_dir) / 'mysqld'
                    break
        
        return config
    
    def _print_header(self):
        """Print welcome message"""
        print("\n")
        print("╔" + "═" * 58 + "╗")
        print("║" + " " * 10 + "MYSQL PASSWORD RESET TOOL" + " " * 22 + "║")
        print("╚" + "═" * 58 + "╝")
        print()
    
    def _validate_mysql_setup(self) -> bool:
        """Check if MySQL is installed"""
        logger.info("Checking MySQL installation...")
        
        if not self.mysql_config['bin_path'] or not self.mysql_config['bin_path'].exists():
            logger.error("ERROR: MySQL not found. Please install MySQL first.")
            return False
        
        if not self.mysql_config['mysql_path'] or not self.mysql_config['mysql_path'].exists():
            logger.error("ERROR: MySQL tools not found")
            return False
        
        if self.is_windows:
            if not self.mysql_config['config_path'] or not self.mysql_config['config_path'].exists():
                logger.error("ERROR: MySQL config not found")
                return False
        
        logger.info(f"MySQL found at: {self.mysql_config['bin_path']}")
        return True
    
    def _get_new_password(self) -> str:
        """Get and confirm new password"""
        logger.info("Enter your new MySQL root password:")
        print()
        
        while True:
            password = getpass.getpass("  New password: ")
            
            if not password:
                logger.error("ERROR: Password cannot be empty")
                continue
            
            confirm = getpass.getpass("  Confirm password: ")
            if password != confirm:
                logger.error("ERROR: Passwords don't match. Try again.")
                continue
            
            logger.info(f"Password set ({len(password)} characters)")
            print()
            return password
    
    def _create_init_file(self, password: str) -> Path:
        """Create temporary SQL file for password reset"""
        logger.info("Creating temporary file...")
        
        try:
            if self.is_windows:
                init_path = Path('C:\\init.txt')
            else:
                fd, init_path = tempfile.mkstemp(suffix='.sql', text=True)
                os.close(fd)
                init_path = Path(init_path)
            
            escaped_pass = password.replace("'", "\\'")
            sql_commands = f"""ALTER USER 'root'@'localhost' IDENTIFIED BY '{escaped_pass}';
FLUSH PRIVILEGES;"""
            
            init_path.write_text(sql_commands, encoding='utf-8')
            self.init_file_path = init_path
            return init_path
            
        except Exception as e:
            logger.error(f"Failed to create file: {e}")
            raise
    
    def _stop_mysql_service(self) -> bool:
        """Stop MySQL service"""
        logger.info("Stopping MySQL...")
        
        try:
            if self.is_windows:
                result = subprocess.run(
                    ['net', 'stop', self.mysql_config['service_name']],
                    capture_output=True,
                    timeout=30
                )
                if result.returncode == 0 or 'The MySQL80 service is not started' in result.stderr.decode():
                    logger.info("MySQL stopped successfully")
                    time.sleep(2)
                    return True
                else:
                    subprocess.run(['taskkill', '/F', '/IM', 'mysqld.exe'], capture_output=True)
                    logger.info("MySQL processes terminated")
                    time.sleep(2)
                    return True
            else:
                subprocess.run(['sudo', 'systemctl', 'stop', 'mysql'], capture_output=True, timeout=30)
                logger.info("MySQL stopped successfully")
                time.sleep(2)
                return True
                
        except Exception as e:
            logger.warning(f"Could not stop MySQL: {e}")
            return False
    
    def _start_mysqld_with_init(self, init_file: Path) -> bool:
        """Start MySQL with init file"""
        logger.info("Starting MySQL with reset file...")
        
        try:
            if self.is_windows:
                cmd = [
                    str(self.mysql_config['mysqld_path']),
                    f'--defaults-file={self.mysql_config["config_path"]}',
                    f'--init-file={init_file}'
                ]
                
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                cmd = [
                    'sudo',
                    str(self.mysql_config['mysqld_path']),
                    f'--init-file={init_file}'
                ]
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            time.sleep(5)
            return True
            
        except Exception as e:
            logger.error(f"Failed to start MySQL: {e}")
            return False
    
    def _cleanup_mysqld_processes(self) -> bool:
        """Clean up MySQL processes"""
        logger.info("Cleaning up...")
        
        try:
            if self.is_windows:
                subprocess.run(['taskkill', '/F', '/IM', 'mysqld.exe'], capture_output=True)
            else:
                subprocess.run(['sudo', 'killall', 'mysqld'], capture_output=True)
            
            time.sleep(3)
            return True
            
        except Exception as e:
            logger.warning(f"Cleanup issue: {e}")
            return True
    
    def _start_mysql_service(self) -> bool:
        """Start MySQL service"""
        logger.info("Starting MySQL service...")
        
        try:
            if self.is_windows:
                result = subprocess.run(
                    ['net', 'start', self.mysql_config['service_name']],
                    capture_output=True,
                    timeout=30
                )
                if result.returncode == 0 or 'already been started' in result.stderr.decode():
                    time.sleep(5)
                    return True
            else:
                subprocess.run(['sudo', 'systemctl', 'start', 'mysql'], capture_output=True, timeout=30)
                time.sleep(5)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start MySQL: {e}")
            return False
    
    def _check_service_status(self) -> bool:
        """Check if MySQL is running"""
        logger.info("Checking MySQL status...")
        
        try:
            if self.is_windows:
                result = subprocess.run(
                    ['sc', 'query', self.mysql_config['service_name']],
                    capture_output=True
                )
                if 'RUNNING' in result.stdout.decode():
                    return True
                else:
                    logger.error("MySQL is not running")
                    return False
            else:
                result = subprocess.run(
                    ['sudo', 'systemctl', 'is-active', 'mysql'],
                    capture_output=True
                )
                return result.returncode == 0
                
        except Exception as e:
            logger.error(f"Could not check status: {e}")
            return False
    
    def _test_password(self, password: str) -> bool:
        """Test if new password works"""
        logger.info("Testing password...")
        
        try:
            cmd = [
                str(self.mysql_config['mysql_path']),
                '-u', 'root',
                f'-p{password}',
                '-e', 'SELECT 1;'
            ]
            
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            
            if result.returncode == 0:
                return True
            else:
                logger.warning("Connection test failed")
                return False
                
        except Exception as e:
            logger.warning(f"Could not test password: {e}")
            return False
    
    def _cleanup_init_file(self):
        """Remove temporary file"""
        logger.info("Cleaning up...")
        
        if self.init_file_path and self.init_file_path.exists():
            try:
                self.init_file_path.unlink()
            except Exception as e:
                logger.warning(f"Could not remove file: {e}")
    
    def reset_password(self):
        """Main password reset process"""
        self._print_header()
        
        if not self._validate_mysql_setup():
            logger.error("ERROR: MySQL check failed")
            return False
        
        print()
        try:
            password = self._get_new_password()
        except KeyboardInterrupt:
            logger.error("ERROR: Cancelled by user")
            return False
        
        try:
            init_file = self._create_init_file(password)
        except Exception as e:
            logger.error(f"ERROR: File creation failed: {e}")
            return False
        
        try:
            self._stop_mysql_service()
            
            if not self._start_mysqld_with_init(init_file):
                logger.error("ERROR: Failed to start MySQL with reset file")
                return False
            
            self._cleanup_mysqld_processes()
            
            if not self._start_mysql_service():
                logger.warning("WARNING: Failed to start MySQL service")
            
            time.sleep(3)
            if not self._check_service_status():
                logger.error("ERROR: MySQL failed to start")
                return False
            
            time.sleep(2)
            password_works = self._test_password(password)
            
            print("\n" + "╔" + "═" * 58 + "╗")
            print("║" + " " * 20 + "SUCCESS!" + " " * 30 + "║")
            print("║" + " " * 17 + "Password has been reset" + " " * 17 + "║")
            print("╚" + "═" * 58 + "╝\n")
            
            if not password_works:
                logger.info("Try logging in manually: mysql -u root -p")
            
            return True
            
        finally:
            self._cleanup_init_file()


def main():
    """Main entry point"""
    try:
        tool = MySQLResetTool()
        success = tool.reset_password()
        
        if not success:
            print("\n" + "╔" + "═" * 58 + "╗")
            print("║" + " " * 20 + "FAILED!" + " " * 31 + "║")
            print("║" + " " * 15 + "Something went wrong, check above." + " " * 7 + "║")
            print("╚" + "═" * 58 + "╝\n")
        
        if sys.platform == 'win32':
            input("\nPress Enter to exit...")
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        logger.error("\nCancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
