# SND 3600 Scanner — Linux Mint

Première version d'une interface graphique dédiée au SilverCrest SND 3600 A2.

## Fonctionnalités

- acquisition directe de `/dev/video0` via V4L2/UVC ;
- résolution maximale 2592×1944 ;
- aperçu live ;
- inversion du négatif couleur ;
- balance des blancs automatique simple ;
- exposition, contraste, luminosité ;
- rotation ;
- export JPEG, PNG ou TIFF ;
- conservation optionnelle du négatif original.

## Installation

```bash
cd snd3600-scanner
chmod +x install.sh
./install.sh
```

Puis :

```bash
snd3600-scanner
```

## Vérification du scanner

Avant de lancer l'application :

```bash
v4l2-ctl --list-devices
v4l2-ctl -d /dev/video0 --get-fmt-video
```

Le scanner doit apparaître comme :

```text
338 Camera
/dev/video0
```

et le mode conseillé est :

```text
2592x1944
YUYV
```

## Important

Le traitement négatif couleur de cette V1 est volontairement simple. Il servira de base pour calibrer une conversion plus élaborée du masque orange à partir de vrais négatifs couleur.
