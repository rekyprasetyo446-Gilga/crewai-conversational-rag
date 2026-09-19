"""
Setup script to configure XAMPP host, Apache reverse proxy, and MySQL memory for multiple agent crew.
Target Host: 10.226.157.87
FastAPI Backend: http://127.0.0.1:8000
Services: Apache (80/443), MySQL (3306), FileZilla (21/14147/50000-50100), Mercury (25/110/143/2224)
"""
import re
import subprocess
from pathlib import Path
import pymysql

XAMPP_DIR = Path("C:/xampp")
HOST_IP = "10.226.157.87"
FASTAPI_PORT = 8000

def update_apache():
    print("[*] Updating Apache configuration...")
    httpd_conf = XAMPP_DIR / "apache/conf/httpd.conf"
    if httpd_conf.exists():
        content = httpd_conf.read_text(encoding="utf-8", errors="ignore")
        
        # 1. Update ServerName
        content = re.sub(r"ServerName\s+localhost:80", f"ServerName {HOST_IP}:80", content)

        # 2. Enable proxy modules
        modules_to_enable = [
            "proxy_module",
            "proxy_http_module",
            "proxy_wstunnel_module",
            "headers_module",
            "rewrite_module",
        ]
        for mod in modules_to_enable:
            pattern = rf"#\s*(LoadModule\s+{mod}\s+modules/mod_{mod.replace('_module', '')}\.so)"
            if re.search(pattern, content):
                content = re.sub(pattern, r"\1", content)
                print(f"  - Enabled Apache module: {mod}")

        # 3. Enable httpd-vhosts.conf inclusion
        vhost_pattern = r"#\s*(Include\s+conf/extra/httpd-vhosts\.conf)"
        if re.search(vhost_pattern, content):
            content = re.sub(vhost_pattern, r"\1", content)
            print("  - Enabled Include conf/extra/httpd-vhosts.conf")

        httpd_conf.write_text(content, encoding="utf-8")
        print("  - Updated httpd.conf successfully")

    # 4. httpd-ssl.conf
    ssl_conf = XAMPP_DIR / "apache/conf/extra/httpd-ssl.conf"
    if ssl_conf.exists():
        content = ssl_conf.read_text(encoding="utf-8", errors="ignore")
        content = re.sub(r"ServerName\s+www\.example\.com:443", f"ServerName {HOST_IP}:443", content)
        ssl_conf.write_text(content, encoding="utf-8")
        print("  - Updated ServerName in httpd-ssl.conf to", f"{HOST_IP}:443")

    # 5. httpd-xampp.conf (Allow remote agents on LAN to access phpMyAdmin & web services)
    xampp_conf = XAMPP_DIR / "apache/conf/extra/httpd-xampp.conf"
    if xampp_conf.exists():
        content = xampp_conf.read_text(encoding="utf-8", errors="ignore")
        content = re.sub(r"Require\s+local", "Require all granted", content)
        xampp_conf.write_text(content, encoding="utf-8")
        print("  - Updated access control in httpd-xampp.conf to 'Require all granted'")

    # 6. Configure httpd-vhosts.conf with reverse proxy for Multiple Agent Crew
    vhosts_conf = XAMPP_DIR / "apache/conf/extra/httpd-vhosts.conf"
    if vhosts_conf.exists():
        vhost_marker = "### CREWAI_AGENT_REVERSE_PROXY ###"
        proxy_config = f"""
{vhost_marker}
<VirtualHost *:80>
    ServerName {HOST_IP}
    ServerAlias localhost 127.0.0.1

    ProxyPreserveHost On
    ProxyTimeout 300

    # Bypass proxy for standard XAMPP management tools and static storage
    ProxyPass /phpmyadmin !
    ProxyPass /dashboard !
    ProxyPass /webalizer !
    ProxyPass /xampp !
    ProxyPass /agent_storage !

    # Route all other traffic to FastAPI Crew backend
    ProxyPass / http://127.0.0.1:{FASTAPI_PORT}/ timeout=300 retry=1
    ProxyPassReverse / http://127.0.0.1:{FASTAPI_PORT}/

    # WebSocket Proxying
    RewriteEngine On
    RewriteCond %{{HTTP:Upgrade}} =websocket [NC]
    RewriteRule /(.*) ws://127.0.0.1:{FASTAPI_PORT}/$1 [P,L]

    ErrorLog "logs/crewai_agent_error.log"
    CustomLog "logs/crewai_agent_access.log" combined
</VirtualHost>
"""
        existing_vhosts = vhosts_conf.read_text(encoding="utf-8", errors="ignore")
        if vhost_marker in existing_vhosts:
            # Replace existing block
            pattern = rf"{vhost_marker}[\s\S]*?</VirtualHost>"
            existing_vhosts = re.sub(pattern, proxy_config.strip(), existing_vhosts)
            vhosts_conf.write_text(existing_vhosts, encoding="utf-8")
            print("  - Refreshed CrewAI Reverse Proxy VirtualHost in httpd-vhosts.conf")
        else:
            vhosts_conf.write_text(existing_vhosts + "\n" + proxy_config, encoding="utf-8")
            print("  - Added CrewAI Reverse Proxy VirtualHost to httpd-vhosts.conf")


def update_mysql():
    print("[*] Updating MySQL configuration...")
    my_ini = XAMPP_DIR / "mysql/bin/my.ini"
    if my_ini.exists():
        content = my_ini.read_text(encoding="utf-8", errors="ignore")
        # Ensure bind-address is set to 0.0.0.0 (all interfaces)
        if "bind-address" in content:
            content = re.sub(r"#?\s*bind-address\s*=\s*\"?127\.0\.0\.1\"?", 'bind-address = "0.0.0.0"', content)
        else:
            content = content.replace("[mysqld]\n", '[mysqld]\nbind-address = "0.0.0.0"\n')
        
        # Ensure sufficient connections for multiple concurrent agents
        if "max_connections" not in content:
            content = content.replace("[mysqld]\n", '[mysqld]\nmax_connections = 250\n')

        my_ini.write_text(content, encoding="utf-8")
        print("  - Set bind-address = \"0.0.0.0\" and max_connections = 250 in my.ini")


def init_mysql_database():
    print("[*] Initializing MySQL 'crewai_memory' database and multi-agent tables...")
    try:
        conn = pymysql.connect(
            host="127.0.0.1",
            user="root",
            password="",
            autocommit=True
        )
        with conn.cursor() as cursor:
            # 1. Create Database
            cursor.execute("CREATE DATABASE IF NOT EXISTS crewai_memory CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            cursor.execute("USE crewai_memory;")

            # 2. Chat Sessions Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                session_id VARCHAR(64) PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                metadata JSON NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # 3. Chat Messages Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                session_id VARCHAR(64) NOT NULL,
                role ENUM('user', 'assistant', 'system') NOT NULL,
                content MEDIUMTEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_session (session_id, created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # 4. Agent Execution Logs Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_execution_logs (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                session_id VARCHAR(64) NOT NULL,
                agent_name VARCHAR(100) NOT NULL,
                task_name VARCHAR(100) NOT NULL,
                status ENUM('pending', 'running', 'completed', 'failed') DEFAULT 'pending',
                input_data MEDIUMTEXT NULL,
                output_data MEDIUMTEXT NULL,
                tool_calls JSON NULL,
                execution_time_ms INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_agent_session (session_id, agent_name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # 5. Shared Blackboard Table (for Agent Collaboration)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS shared_blackboard (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                session_id VARCHAR(64) NOT NULL,
                source_agent VARCHAR(100) NOT NULL,
                key_name VARCHAR(100) NOT NULL,
                value_data MEDIUMTEXT NOT NULL,
                tags VARCHAR(255) NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY uq_session_key (session_id, key_name),
                INDEX idx_session_bb (session_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # 6. User setup for remote agents
            try:
                cursor.execute("CREATE USER IF NOT EXISTS 'crew_agent'@'%' IDENTIFIED BY 'AgentSecurePass123!';")
                cursor.execute("GRANT ALL PRIVILEGES ON crewai_memory.* TO 'crew_agent'@'%';")
                cursor.execute("FLUSH PRIVILEGES;")
                print("  - Created user 'crew_agent'@'%' with full permissions on crewai_memory")
            except Exception as user_e:
                print(f"  - Note on user creation: {user_e}")

            print("  - Database 'crewai_memory' and tables initialized successfully.")
        conn.close()
    except Exception as e:
        print(f"  [!] MySQL initialization error: {e}")


def restart_apache():
    print("[*] Testing and reloading Apache service...")
    httpd_exe = XAMPP_DIR / "apache/bin/httpd.exe"
    if not httpd_exe.exists():
        print("  [!] httpd.exe not found at expected path.")
        return

    # Check syntax first
    test_result = subprocess.run(
        [str(httpd_exe), "-t"],
        capture_output=True,
        text=True
    )
    if "Syntax OK" in test_result.stderr or "Syntax OK" in test_result.stdout:
        print("  - Apache configuration syntax is valid (Syntax OK).")
    else:
        print(f"  [!] Apache syntax warning/error:\n{test_result.stderr or test_result.stdout}")

    # Restart Apache gracefully or restart process
    try:
        subprocess.run(
            ["powershell", "-Command", "Get-Process httpd -ErrorAction SilentlyContinue | Stop-Process -Force"],
            capture_output=True,
            timeout=10
        )
        print("  - Stopped previous httpd processes.")
    except Exception as e:
        print(f"  - Error stopping httpd: {e}")

    # Launch Apache via xampp apache_start.bat or httpd.exe
    try:
        apache_start = XAMPP_DIR / "apache_start.bat"
        if apache_start.exists():
            subprocess.Popen(["cmd.exe", "/c", str(apache_start)], cwd=str(XAMPP_DIR))
        else:
            subprocess.Popen([str(httpd_exe)], cwd=str(XAMPP_DIR / "apache"))
        print("  - Restarted Apache daemon successfully.")
    except Exception as e:
        print(f"  [!] Failed to restart Apache: {e}")


def update_filezilla():
    print("[*] Updating FileZilla FTP Server configuration...")
    # Ensure agent shared storage directory exists in htdocs for dual FTP + HTTP access
    storage_dir = XAMPP_DIR / "htdocs/agent_storage"
    storage_dir.mkdir(parents=True, exist_ok=True)
    storage_path_str = str(storage_dir).replace("/", "\\")

    # b212f672104c29a95d91807e12c4abe5 is MD5 of "AgentSecurePass123!"
    fz_xml_content = f"""<FileZillaServer>
    <Settings>
        <Item name="Server port" type="numeric">21</Item>
        <Item name="Admin port" type="numeric">14147</Item>
        <Item name="Custom PASV IP type" type="numeric">1</Item>
        <Item name="Custom PASV IP" type="string">{HOST_IP}</Item>
        <Item name="Custom PASV min port" type="numeric">50000</Item>
        <Item name="Custom PASV max port" type="numeric">50100</Item>
    </Settings>
    <Groups />
    <Users>
        <User Name="crew_agent">
            <Option Name="Pass">b212f672104c29a95d91807e12c4abe5</Option>
            <Option Name="Group" />
            <Option Name="Bypass server userlimit">0</Option>
            <Option Name="User Limit">0</Option>
            <Option Name="IP Filter Allowed" />
            <Option Name="IP Filter Disallowed" />
            <Option Name="Enabled">1</Option>
            <Option Name="Comments">Dedicated multi-agent shared storage user</Option>
            <Option Name="ForceSsl">0</Option>
            <IpFilter>
                <Disallowed />
                <Allowed />
            </IpFilter>
            <Permissions>
                <Permission Dir="{storage_path_str}">
                    <Option Name="FileRead">1</Option>
                    <Option Name="FileWrite">1</Option>
                    <Option Name="FileDelete">1</Option>
                    <Option Name="FileAppend">1</Option>
                    <Option Name="DirCreate">1</Option>
                    <Option Name="DirDelete">1</Option>
                    <Option Name="DirList">1</Option>
                    <Option Name="DirSubdirs">1</Option>
                    <Option Name="IsHome">1</Option>
                    <Option Name="AutoCreate">0</Option>
                </Permission>
            </Permissions>
            <SpeedLimits DlType="0" DlLimit="10" UlType="0" UlLimit="10">
                <Download />
                <Upload />
            </SpeedLimits>
        </User>
        <User Name="anonymous">
            <Option Name="Pass" />
            <Option Name="Group" />
            <Option Name="Bypass server userlimit">0</Option>
            <Option Name="User Limit">0</Option>
            <Option Name="IP Filter Allowed" />
            <Option Name="IP Filter Disallowed" />
            <Option Name="Enabled">1</Option>
            <Option Name="Comments">Anonymous read-only access</Option>
            <Option Name="ForceSsl">0</Option>
            <IpFilter>
                <Disallowed />
                <Allowed />
            </IpFilter>
            <Permissions>
                <Permission Dir="{storage_path_str}">
                    <Option Name="FileRead">1</Option>
                    <Option Name="FileWrite">0</Option>
                    <Option Name="FileDelete">0</Option>
                    <Option Name="FileAppend">0</Option>
                    <Option Name="DirCreate">0</Option>
                    <Option Name="DirDelete">0</Option>
                    <Option Name="DirList">1</Option>
                    <Option Name="DirSubdirs">1</Option>
                    <Option Name="IsHome">1</Option>
                    <Option Name="AutoCreate">0</Option>
                </Permission>
            </Permissions>
            <SpeedLimits DlType="0" DlLimit="10" UlType="0" UlLimit="10">
                <Download />
                <Upload />
            </SpeedLimits>
        </User>
    </Users>
</FileZillaServer>
"""
    for file_name in ["FileZilla Server.xml", "FileZillaServer.xml"]:
        xml_path = XAMPP_DIR / f"FileZillaFTP/{file_name}"
        if xml_path.parent.exists():
            xml_path.write_text(fz_xml_content, encoding="utf-8")
            print(f"  - Configured {file_name} with user 'crew_agent' and home '{storage_path_str}'")


def update_mercury():
    print("[*] Updating Mercury Mail configuration...")
    mercury_ini = XAMPP_DIR / "MercuryMail/MERCURY.INI"
    if mercury_ini.exists():
        content = mercury_ini.read_text(encoding="utf-8", errors="ignore")
        content = re.sub(r"myname:\s+localhost", f"myname:          {HOST_IP}", content)
        if f"{HOST_IP}  :  {HOST_IP}" not in content:
            domains_pattern = r"(\[Domains\][\s\S]*?)(localhost\s+:\s+localhost\.com)"
            replacement = r"\1\2\nlocalhost  :  " + HOST_IP + r"\n" + HOST_IP + r"  :  " + HOST_IP
            content = re.sub(domains_pattern, replacement, content)
        mercury_ini.write_text(content, encoding="utf-8")
        print(f"  - Updated MERCURY.INI with Host {HOST_IP} and domain routes")

    # Add crew_agent to PMAIL.USR and create mailbox directory
    mail_dir = XAMPP_DIR / "MercuryMail/MAIL"
    if mail_dir.exists():
        pmail_usr = mail_dir / "PMAIL.USR"
        agent_line = "U;crew_agent;CrewAI Multi-Agent Coordinator\n"
        if pmail_usr.exists():
            pmail_content = pmail_usr.read_text(encoding="utf-8", errors="ignore")
            if "crew_agent" not in pmail_content:
                pmail_usr.write_text(pmail_content + agent_line, encoding="utf-8")
                print("  - Registered 'crew_agent' in PMAIL.USR")
        else:
            pmail_usr.write_text("A;Admin;Mail System Administrator\n" + agent_line, encoding="utf-8")
            print("  - Created PMAIL.USR with 'crew_agent'")

        agent_mailbox = mail_dir / "crew_agent"
        agent_mailbox.mkdir(parents=True, exist_ok=True)
        print("  - Initialized mailbox folder for 'crew_agent'")



def update_xampp_control():
    print("[*] Updating XAMPP Control configuration...")
    control_ini = XAMPP_DIR / "xampp-control.ini"
    if control_ini.exists():
        try:
            content = control_ini.read_text(encoding="utf-8", errors="ignore")
            if "[ServicePorts]" not in content:
                content += """
[Services]
Apache=1
MySQL=1
FileZilla=1
Mercury=1
Tomcat=0

[ServicePorts]
Apache=80
ApacheSSL=443
MySQL=3306
FileZilla=21
FileZillaAdmin=14147
Mercury1=25
Mercury2=110
Mercury3=143
Mercury4=2224
"""
                control_ini.write_text(content, encoding="utf-8")
                print("  - Added ServicePorts configuration to xampp-control.ini")
            else:
                print("  - xampp-control.ini already has ServicePorts configured.")
        except Exception as e:
            print(f"  - Note: xampp-control.ini could not be modified (XAMPP GUI may be open): {e}")




if __name__ == "__main__":
    print(f"=== Configuring XAMPP for Multiple Agent Crew (Host: {HOST_IP}) ===")
    update_apache()
    update_mysql()
    init_mysql_database()
    restart_apache()
    update_filezilla()
    update_mercury()
    update_xampp_control()
    print("\n[SUCCESS] XAMPP Apache Gateway and MySQL Memory setup completed successfully!")

