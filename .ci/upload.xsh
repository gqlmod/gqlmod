#!/usr/bin/xonsh
from urllib.request import urlopen, Request
import zipfile

$RAISE_SUBPROC_ERROR = True

ARTIFACTS_URL = f"https://api.cirrus-ci.com/v1/artifact/build/{$CIRRUS_BUILD_ID}/build/dist.zip"
PYPI_TEST_REPO = "https://test.pypi.org/legacy/"
PYPI_PROD_REPO = "https://pypi.org/legacy/"


with tempfile.TemporaryDirectory() as td:
    cd @(td.name)

    with zipfile.ZipFile(urlopen(ARTIFACTS_URL)) as zf:
        zf.extractall()

dists = [f for f in pg`**` if '+' not in f.name]

print("Found dists:", *dists)

print("Uploading to test repo...")

twine upload \
    --repository-url @(PYPI_TEST_REPO) \
    --username __token__ \
    --password "$TWINE_TEST_TOKEN" \
    @(dists)


print("")

if $CIRRUS_RELEASE:
    print("Uploading to GitHub...")
    for dist in dists:
        print(f"\t{dist.name}...")
        dest_url = f"https://uploads.github.com/repos/{$CIRRUS_REPO_FULL_NAME}/releases/{$CIRRUS_RELEASE}/assets?name={dist.name}"
        with dist.open('rb') as fobj:
            with urlopen(Request(
                url=dest_url,
                method='POST'
                data=fobj,
                headers={
                    "Authorization": f"token {$GITHUB_TOKEN}",
                    "Content-Type": "application/octet-stream",
                },
            )) as resp:
                if resp.getcode() >= 400:
                    print(f"Error: {resp.getcode()}")
                    print(str(resp.info()))
                    sys.exit(1)

    print("")

    print("Uploading to PyPI...")
    twine upload \
        --repository-url @(PYPI_PROD_REPO) \
        --username __token__ \
        --password "$TWINE_PROD_TOKEN" \
        @(dists)
