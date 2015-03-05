pip="${VENV}/bin/pip"
alembic="${VENV}/bin/alembic"

cd "${INSTALLDIR}/${REPO}/"

$pip install -e "${INSTALLDIR}/${REPO}/"
$alembic upgrade head
