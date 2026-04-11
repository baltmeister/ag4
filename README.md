# Mirronline

Dies ist das Haupt-Repository des Mirror-Online-Projekts, einer Plattform, die eine Online-Forum-Umgebung für Forschungszwecke simuliert. Inspiriert von Spiegel Online, ermöglicht sie Forschenden die Analyse komplexer Interaktionen und Verhaltensmuster in einer kontrollierten Umgebung.

## Nutzung des Tools

Mehr Informationen zu verwendeten Tools, Software-Aufbau, Deployment uvm. befinden sich im Ordner [documentation](./documentation) dieses Repositories.

#### 1. **Virtualenv und Python 3 installieren**
Die Installation hängt von deinem Betriebssystem ab. Unter Linux (z. B. Ubuntu) kannst du folgende Befehle verwenden:

```shell
sudo apt install python3 python3-pip
sudo pip install virtualenv
```

#### 2. Repository klonen

Öffne ein Terminal und gib folgenden Befehl ein, um das Repo zu klonen und ins Projektverzeichnis wechseln

```sh
git clone https://github.com/Julreut/ag4.git
cd ag4
```
→ Dieser Befehl lädt den Quellcode von GitHub herunter und wechselt in das Projektverzeichnis.

#### 3. Virtuelle Umgebung erstellen, aktivieren und Abhängigkeiten installieren

Erstelle eine virtuelle Umgebung und aktiviere sie:

```sh
virtualenv .venv
source .venv/bin/activate
```

Installiere die erforderlichen Abhängigkeiten:

```sh
pip install -r requirements.txt
```

#### 5. Static Files einsammeln

Sammle die statischen Dateien, damit sie in einer Produktionsumgebung bereitgestellt werden können:

```sh
python ./src/manage.py collectstatic
```

#### 6. Demo Daten nutzen
// Um die Demo Daten in der manuellen Ausführung des Programms zu nutzen, gehe in die `settings.py` File und setze `DATA_DIRECTORY` auf `data.demo`:

```python
# für die Nutzung der Demo-Daten:
DATA_DIRECTORY = "data.demo" # Lokales Debugging
# Datenverzeichnis
# DATA_DIRECTORY = os.environ['DATA_DIRECTORY'] if 'DATA_DIRECTORY' in os.environ else "data"

# Datenbank
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
  'default': {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': os.path.join(DATA_DIRECTORY, 'db.sqlite3'),
  }
```

#### 7. Migrations ausführen

Führe die Datenbankmigrationen aus, um die Datenbanktabellen zu erstellen:

```sh
python ./src/manage.py migrate
```
#### 8. Server starten

Entwicklungsserver starten.
```sh
python ./src/manage.py runserver 127.0.0.1:8000
```

Mit diesen Schritten kannst du die Software manuell auf deinem lokalen System bereitstellen. Dies ist besonders nützlich für Entwicklungs-  und Testzwecke. Stelle sicher, dass Python 3 und Virtualenv installiert sind, bevor du beginnst. Falls du Fragen hast oder auf Probleme stößt, konsultiere die Dokumentation oder wende dich an das Entwicklerteam. 😊


### Hinweise der Fakebook-Autoren zum Deployment:

- When using our tool for research purposes, please cite our paper: Voggenreiter, A; Brandt S; Putterer, F; Frings, A and Pfeffer J. The Role of Likes: How Online Feedback Impacts Users' Mental Health (2023).
  https://arxiv.org/abs/2312.11914

- Fakebook allows to setup a Social-Media-Environment, in which users can interact freely. Every interaction can be watched and controlled by the project maintainer (e.g. the researcher). The project maintainer is responsible for everything happening on his or her social media environment. The tool should be used in an ethical responsible manner. Study participants and other users of the social media environment have to be informed that all of their data can be inspected by the project maintainer. The project maintainers are responsible for clarifying the standards of acceptable and hatefree behavior and are expected to take appropriate and fair corrective action in response to any instances of unacceptable behavior. Project maintainers have the right and responsibility to remove, edit, or reject posts and comments, or to ban temporarily or permanently any user for other behaviors that they deem inappropriate, threatening, offensive, illegal or harmful.
