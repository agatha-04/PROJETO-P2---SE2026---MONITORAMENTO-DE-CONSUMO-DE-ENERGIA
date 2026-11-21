#!/bin/sh
set -e
cd $(dirname $0)/..
docker buildx create --name energiabuilder --use 2>/dev/null || docker buildx use energiabuilder
docker buildx inspect --bootstrap
docker buildx build --platform linux/arm64 -f docker/Dockerfile -t energia-app:1.0 --load application/
docker image inspect energia-app:1.0 --format '{{.Architecture}}/{{.Os}}'
OUT=buildroot-external/board/energia/rootfs-overlay/opt/docker
docker save energia-app:1.0 -o $OUT/energia-app.tar
sha256sum $OUT/energia-app.tar | tee docs/energia-app.tar.sha256
