#!/usr/bin/env python3
import socket
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def clear_screen():
    """Clear terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    """Display ASCII art banner"""
    banner = f"""
{Colors.CYAN}{Colors.BOLD}
    ██████╗  ██████╗ ██████╗ ████████╗    ███████╗ ██████╗ █████╗ ███╗   ██╗███╗   ██╗███████╗██████╗ 
    ██╔══██╗██╔═══██╗██╔══██╗╚══██╔══╝    ██╔════╝██╔════╝██╔══██╗████╗  ██║████╗  ██║██╔════╝██╔══██╗
    ██████╔╝██║   ██║██████╔╝   ██║       ███████╗██║     ███████║██╔██╗ ██║██╔██╗ ██║█████╗  ██████╔╝
    ██╔═══╝ ██║   ██║██╔══██╗   ██║       ╚════██║██║     ██╔══██║██║╚██╗██║██║╚██╗██║██╔══╝  ██╔══██╗
    ██║     ╚██████╔╝██║  ██║   ██║       ███████║╚██████╗██║  ██║██║ ╚████║██║ ╚████║███████╗██║  ██║
    ╚═╝      ╚═════╝ ╚═╝  ╚═╝   ╚═╝       ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝
{Colors.END}
{Colors.YELLOW}                                    Advanced TCP Port Scanner v2.0{Colors.END}
{Colors.MAGENTA}                                      Author: Security Tools{Colors.END}
{Colors.RED}                                   ⚠️  For Educational Purposes Only ⚠️{Colors.END}

{Colors.BLUE}{'═' * 90}{Colors.END}
"""
    print(banner)

def print_loading_animation():
    """Display loading animation"""
    print(f"{Colors.YELLOW}[*] Initializing scanner", end="")
    for _ in range(5):
        time.sleep(0.3)
        print(".", end="", flush=True)
    print(f" Done!{Colors.END}")
    time.sleep(0.5)

class PortScanner:
    def __init__(self, timeout=1.0, max_threads=100):
        self.timeout = timeout
        self.max_threads = max_threads
        self.open_ports = []
        self.closed_ports = []
        self.lock = threading.Lock()
        self.scanned_count = 0
        self.total_ports = 0
    
    def scan_port(self, ip, port):
        """Scan a single port on the given IP"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(self.timeout)
                result = sock.connect_ex((ip, port))
                
                with self.lock:
                    self.scanned_count += 1
                    
                if result == 0:
                    with self.lock:
                        self.open_ports.append(port)
                    return port, True
                else:
                    with self.lock:
                        self.closed_ports.append(port)
                    return port, False
        except socket.error:
            with self.lock:
                self.closed_ports.append(port)
                self.scanned_count += 1
            return port, False
    
    def print_progress(self, current, total):
        """Print progress bar"""
        percent = (current / total) * 100
        bar_length = 40
        filled_length = int(bar_length * current // total)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        
        print(f'\r{Colors.BLUE}[{bar}] {percent:.1f}% ({current}/{total}){Colors.END}', end='', flush=True)
    
    def scan_ip(self, ip, start_port, end_port, show_closed=False):
        """Scan IP address with threading"""
        print(f'{Colors.GREEN}[*] Target: {Colors.BOLD}{ip}{Colors.END}')
        print(f'{Colors.GREEN}[*] Port Range: {Colors.BOLD}{start_port}-{end_port}{Colors.END}')
        print(f'{Colors.GREEN}[*] Threads: {Colors.BOLD}{self.max_threads}{Colors.END}')
        print(f'{Colors.GREEN}[*] Timeout: {Colors.BOLD}{self.timeout}s{Colors.END}')
        print(f'{Colors.BLUE}{"─" * 60}{Colors.END}')
        
        start_time = time.time()
        self.open_ports = []
        self.closed_ports = []
        self.scanned_count = 0
        self.total_ports = end_port - start_port + 1
        
        print(f'{Colors.YELLOW}[*] Starting scan...{Colors.END}')
        
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            # Submit all port scan tasks
            futures = {
                executor.submit(self.scan_port, ip, port): port 
                for port in range(start_port, end_port + 1)
            }
            
            # Process completed tasks
            for future in as_completed(futures):
                port, is_open = future.result()
                
                # Update progress
                self.print_progress(self.scanned_count, self.total_ports)
                
                if is_open:
                    service = self.get_service_name(port)
                    print(f'\n{Colors.GREEN}[+] {ip}:{port}/TCP Open {Colors.BOLD}{service}{Colors.END}')
                elif show_closed:
                    print(f'\n{Colors.RED}[-] {ip}:{port}/TCP Closed{Colors.END}')
        
        print()  # New line after progress bar
        end_time = time.time()
        
        # Print summary
        self.print_summary(ip, end_time - start_time)
        
        return sorted(self.open_ports)
    
    def scan_domain(self, domain, start_port, end_port, show_closed=False):
        """Resolve domain and scan the IP"""
        try:
            print(f'{Colors.YELLOW}[*] Resolving domain {Colors.BOLD}{domain}{Colors.END}...', end='')
            ip = socket.gethostbyname(domain)
            print(f' {Colors.GREEN}✓{Colors.END}')
            print(f'{Colors.CYAN}[*] {domain} → {ip}{Colors.END}')
            return self.scan_ip(ip, start_port, end_port, show_closed)
        except socket.gaierror as e:
            print(f' {Colors.RED}✗{Colors.END}')
            print(f'{Colors.RED}[!] Error resolving domain {domain}: {e}{Colors.END}')
            return []
    
    def print_summary(self, target, scan_time):
        """Print scan summary"""
        print(f'{Colors.BLUE}{"═" * 60}{Colors.END}')
        print(f'{Colors.BOLD}SCAN SUMMARY{Colors.END}')
        print(f'{Colors.BLUE}{"─" * 60}{Colors.END}')
        print(f'{Colors.WHITE}Target: {Colors.BOLD}{target}{Colors.END}')
        print(f'{Colors.WHITE}Scan Time: {Colors.BOLD}{scan_time:.2f} seconds{Colors.END}')
        print(f'{Colors.WHITE}Total Ports: {Colors.BOLD}{self.total_ports}{Colors.END}')
        print(f'{Colors.GREEN}Open Ports: {Colors.BOLD}{len(self.open_ports)}{Colors.END}')
        print(f'{Colors.RED}Closed Ports: {Colors.BOLD}{len(self.closed_ports)}{Colors.END}')
        
        if self.open_ports:
            print(f'{Colors.CYAN}{"─" * 60}{Colors.END}')
            print(f'{Colors.BOLD}OPEN PORTS DETAILS{Colors.END}')
            print(f'{Colors.CYAN}{"─" * 60}{Colors.END}')
            for port in sorted(self.open_ports):
                service = self.get_service_name(port)
                print(f'{Colors.GREEN}  {port}/TCP {Colors.WHITE}{service}{Colors.END}')
        
        print(f'{Colors.BLUE}{"═" * 60}{Colors.END}')
    
    def get_service_name(self, port):
        """Get common service name for port"""
        common_ports = {
            21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
            80: "HTTP", 110: "POP3", 135: "RPC", 139: "NetBIOS", 143: "IMAP",
            443: "HTTPS", 445: "SMB", 993: "IMAPS", 995: "POP3S", 1723: "PPTP",
            3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL", 5900: "VNC",
            6379: "Redis", 8080: "HTTP-Alt", 8443: "HTTPS-Alt", 27017: "MongoDB"
        }
        return common_ports.get(port, "Unknown")

def validate_port_range(start_port, end_port):
    """Validate port range"""
    if not (1 <= start_port <= 65535) or not (1 <= end_port <= 65535):
        raise ValueError("Ports must be between 1 and 65535")
    if start_port > end_port:
        raise ValueError("Start port must be less than or equal to end port")

def print_usage():
    """Print usage information"""
    usage = f"""
{Colors.YELLOW}USAGE:{Colors.END}
    python port_scanner.py <target> <start_port> <end_port> [options]

{Colors.YELLOW}OPTIONS:{Colors.END}
    --domain, -d      Treat target as domain name
    --timeout <n>     Socket timeout in seconds (default: 1.0)
    --threads <n>     Number of threads (default: 100)
    --show-closed     Show closed ports
    --verbose         Verbose output
    --help, -h        Show this help message

{Colors.YELLOW}EXAMPLES:{Colors.END}
    python port_scanner.py 192.168.1.1 1 1000
    python port_scanner.py google.com 80 443 --domain
    python port_scanner.py 127.0.0.1 20 80 --timeout 2.0 --threads 50 --verbose
    python port_scanner.py scanme.nmap.org 1 1000 --domain --show-closed

{Colors.RED}DISCLAIMER:{Colors.END}
    This tool is for educational and authorized testing purposes only.
    Do not use this tool against systems you do not own or have permission to test.
"""
    print(usage)

def main():
    # Clear screen and show banner
    clear_screen()
    print_banner()
    
    # Check for help
    if len(sys.argv) < 2 or '--help' in sys.argv or '-h' in sys.argv:
        print_usage()
        sys.exit(0)
    
    # Check minimum arguments
    if len(sys.argv) < 4:
        print(f"{Colors.RED}[!] Error: Missing required arguments{Colors.END}")
        print_usage()
        sys.exit(1)
    
    # Parse basic arguments
    target = sys.argv[1]
    try:
        start_port = int(sys.argv[2])
        end_port = int(sys.argv[3])
    except ValueError:
        print(f"{Colors.RED}[!] Error: Start and end ports must be integers{Colors.END}")
        sys.exit(1)
    
    # Parse optional arguments
    is_domain = '--domain' in sys.argv or '-d' in sys.argv
    show_closed = '--show-closed' in sys.argv
    verbose = '--verbose' in sys.argv
    
    # Parse timeout
    timeout = 1.0
    if '--timeout' in sys.argv:
        try:
            timeout_idx = sys.argv.index('--timeout')
            timeout = float(sys.argv[timeout_idx + 1])
        except (IndexError, ValueError):
            print(f"{Colors.RED}[!] Error: Invalid timeout value{Colors.END}")
            sys.exit(1)
    
    # Parse threads
    max_threads = 100
    if '--threads' in sys.argv:
        try:
            threads_idx = sys.argv.index('--threads')
            max_threads = int(sys.argv[threads_idx + 1])
            if max_threads > 1000:
                print(f"{Colors.YELLOW}[!] Warning: High thread count may cause issues{Colors.END}")
        except (IndexError, ValueError):
            print(f"{Colors.RED}[!] Error: Invalid threads value{Colors.END}")
            sys.exit(1)
    
    # Show loading animation
    print_loading_animation()
    
    try:
        # Validate inputs
        validate_port_range(start_port, end_port)
        
        # Create scanner instance
        scanner = PortScanner(timeout=timeout, max_threads=max_threads)
        
        # Perform scan
        if is_domain:
            open_ports = scanner.scan_domain(target, start_port, end_port, show_closed)
        else:
            # Validate IP format if not domain
            try:
                socket.inet_aton(target)  # Raises exception for invalid IP
            except socket.error:
                print(f"{Colors.RED}[!] Invalid IP address: {target}{Colors.END}")
                print(f"{Colors.YELLOW}[!] Use --domain flag if this is a domain name{Colors.END}")
                sys.exit(1)
            open_ports = scanner.scan_ip(target, start_port, end_port, show_closed)
        
        # Final message
        if open_ports:
            print(f"{Colors.GREEN}[✓] Scan completed successfully!{Colors.END}")
        else:
            print(f"{Colors.YELLOW}[!] No open ports found in the specified range{Colors.END}")
                
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}[!] Scan interrupted by user{Colors.END}")
        print(f"{Colors.YELLOW}[*] Partial results may be available above{Colors.END}")
        sys.exit(1)
    except ValueError as e:
        print(f"{Colors.RED}[!] Input error: {e}{Colors.END}")
        sys.exit(1)
    except socket.error as e:
        print(f"{Colors.RED}[!] Network error: {e}{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"{Colors.RED}[!] Unexpected error: {e}{Colors.END}")
        sys.exit(1)

if __name__ == '__main__':
    main()