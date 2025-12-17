# Codigo del proyecto Padel Pro

```bash
python3 -m venv .venv && source .venv/bin/activate
```

```bash
pip install -r requirements.txt
```

```bash
python3 main.py
```

```bash
sudo mysql -e "CREATE USER 'padelpro'@'localhost' IDENTIFIED BY 'padelpro123';"
sudo mysql -e "GRANT ALL PRIVILEGES ON padelpro.* TO 'padelpro'@'localhost';"
sudo mysql -e "FLUSH PRIVILEGES;"
sudo mysql -e "CREATE DATABASE padelpro;"
```