pip="${VENV}/bin/pip"
alembic="${VENV}/bin/alembic"

cd "${INSTALLDIR}/${REPO}/"

$pip install -e "${INSTALLDIR}/${REPO}/"
PYRAMID_CONFIG_FILE="${INSTALLDIR}/${REPO}/production.ini" $alembic upgrade head
