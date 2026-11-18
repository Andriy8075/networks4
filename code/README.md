# ЛР4. Скрипти захоплення та аналізу трафіку

Скрипти працюють із **готовим Compose ЛР1** (`../lab1/code`). Новий Docker-стек не піднімається.

Середовище: **WSL/Ubuntu** (там, де крутиться Docker Engine). PCAP потім відкривайте у **Wireshark на Windows**.

## Підготовка

```bash
cd /mnt/c/Users/Admin/projects/NetworkLabs/lab1/code
docker compose up -d --build
docker compose ps
```

Установіть інструменти в WSL, якщо їх немає:

```bash
sudo apt-get update
sudo apt-get install -y tcpdump dnsutils curl
# опційно для analyze_pcap.py:
sudo apt-get install -y tshark
pip install -r /mnt/c/Users/Admin/projects/NetworkLabs/lab4/code/requirements.txt
```

Зробіть скрипти виконуваними:

```bash
cd /mnt/c/Users/Admin/projects/NetworkLabs/lab4/code
chmod +x *.sh
```

## Порядок запуску (максимальний бал)

```bash
./01_check_lab1.sh
./02_capture_normal.sh
./03_capture_database.sh
./04_break_nginx_port.sh
./05_capture_failure.sh
./06_restore_nginx_port.sh
./07_capture_recovered.sh
```

Артефакти з’являться в `../evidence/pcaps/`, `../evidence/console/`, `../evidence/nginx/`.

## Швидкий розбір PCAP

```bash
python3 analyze_pcap.py ../evidence/pcaps/normal.pcap
python3 analyze_pcap.py ../evidence/pcaps/database.pcap --redis
python3 analyze_pcap.py ../evidence/pcaps/failure.pcap --failure
python3 analyze_pcap.py ../evidence/pcaps/recovered.pcap
```

Скрипт друкує кандидати номерів пакетів (DNS Transaction ID, TCP handshake, HTTP, Redis, 502/RST). Остаточно перевіряйте їх у Wireshark.

## Важливо

- `04_break_nginx_port.sh` змінює `lab1/code/nginx.conf`. Завжди завершуйте `06_restore_nginx_port.sh`.
- Захоплення йде через `nsenter` у netns контейнера `proxy` або `db`, інтерфейс `any`.
- Хост-порт проксі: `http://127.0.0.1:8080/`.
