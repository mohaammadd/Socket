#!/usr/bin/env python3
import socket
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

class PortScanner:
    def __init__(self, timeout=1.0, max_threads=100):
        self.timeout = timeout
        self.max_threads = max_threads
        self.open_ports = []
        self.lock = threading.Lock()
    
    def scan_port(self, ip, port):
        """Scan a single port on the given IP"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(self.timeout)
                result = sock.connect_ex((ip, port))
                if result == 0:
                    with self.lock:
                        self.open_ports.append(port)
                    return port, True
                return port, False
        except socket.error:
            return port, False
    
    def scan_ip(self, ip, start_port, end_port, show_closed=False):
        """Scan IP address with threading"""
        print(f'[*] Starting TCP port scan on {ip}')
        print(f'[*] Scanning ports {start_port}-{end_port}')
        
        start_time = time.time()
        self.open_ports = []
        
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            # Submit all port scan tasks
            futures = {
                executor.submit(self.scan_port, ip, port): port 
                for port in range(start_port, end_port + 1)
            }
            
            # Process completed tasks
            for future in as_completed(futures):
                port, is_open = future.result()
                if is_open:
                    service = self.get_service_name(port)
                    print(f"[+] {ip}:{port}/TCP Open {service}")
                elif show_closed:
                    print(f"[-] {ip}:{port}/TCP Closed")
        
        end_time = time.time()
        print(f'[*] Scan completed in {end_time - start_time:.2f} seconds')
        print(f'[*] Found {len(self.open_ports)} open ports')
        
        return sorted(self.open_ports)
    
    def scan_domain(self, domain, start_port, end_port, show_closed=False):
        """Resolve domain and scan the IP"""
        try:
            print(f'[*] Resolving domain {domain}...')
            ip = socket.gethostbyname(domain)
            print(f'[*] Domain {domain} resolved to {ip}')
            return self.scan_ip(ip, start_port, end_port, show_closed)
        except socket.gaierror as e:
            print(f'[!] Error resolving domain {domain}: {e}')
            return []
    
    def get_service_name(self, port):
        """Get common service name for port"""
        common_ports = {
            21: "(FTP)", 22: "(SSH)", 23: "(Telnet)", 25: "(SMTP)",
            53: "(DNS)", 80: "(HTTP)", 110: "(POP3)", 143: "(IMAP)",
            443: "(HTTPS)", 993: "(IMAPS)", 995: "(POP3S)", 
            3389: "(RDP)", 5432: "(PostgreSQL)", 3306: "(MySQL)"
        }
        return common_ports.get(port, "")

def validate_port_range(start_port, end_port):
    """Validate port range"""
    if not (1 <= start_port <= 65535) or not (1 <= end_port <= 65535):
        raise ValueError("Ports must be between 1 and 65535")
    if start_port > end_port:
        raise ValueError("Start port must be less than or equal to end port")

def main():
    # Simple argument parsing
    if len(sys.argv) < 4:
        print("Usage: python port_scanner_base.py <target> <start_port> <end_port> [options]")
        print("\nOptions:")
        print("  --domain, -d      Treat target as domain name")
        print("  --timeout <n>     Socket timeout in seconds (default: 1.0)")
        print("  --threads <n>     Number of threads (default: 100)")
        print("  --show-closed     Show closed ports")
        print("  --verbose         Verbose output")
        print("\nExamples:")
        print("  python port_scanner_base.py 192.168.1.1 1 1000")
        print("  python port_scanner_base.py google.com 80 443 --domain")
        sys.exit(1)
    
    # Parse basic arguments
    target = sys.argv[1]
    try:
        start_port = int(sys.argv[2])
        end_port = int(sys.argv[3])
    except ValueError:
        print("[!] Error: Start and end ports must be integers")
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
            print("[!] Error: Invalid timeout value")
            sys.exit(1)
    
    # Parse threads
    max_threads = 100
    if '--threads' in sys.argv:
        try:
            threads_idx = sys.argv.index('--threads')
            max_threads = int(sys.argv[threads_idx + 1])
        except (IndexError, ValueError):
            print("[!] Error: Invalid threads value")
            sys.exit(1)
    
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
                print(f"[!] Invalid IP address: {target}")
                print("[!] Use --domain flag if this is a domain name")
                sys.exit(1)
            open_ports = scanner.scan_ip(target, start_port, end_port, show_closed)
        
        # Summary
        if open_ports and verbose:
            print(f"\n[*] Summary: Open ports on {target}:")
            for port in open_ports:
                service = scanner.get_service_name(port)
                print(f"    {port}/TCP {service}")
                
    except KeyboardInterrupt:
        print("\n[!] Scan interrupted by user")
        sys.exit(1)
    except ValueError as e:
        print(f"[!] Input error: {e}")
        sys.exit(1)
    except socket.error as e:
        print(f"[!] Network error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[!] Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()