#!/bin/bash
# Breaking Bad Habits - Debian Build Script (Venv Fix)

APP_NAME="breakingbadhabits"
VERSION="1.0"
BUILD_DIR="build_package"
PACKAGE_DIR="${BUILD_DIR}/${APP_NAME}_${VERSION}"

echo "Building Debian package for ${APP_NAME} v${VERSION}..."

# 1. Clean previous builds
rm -rf "$BUILD_DIR"
mkdir -p "$PACKAGE_DIR/DEBIAN"
mkdir -p "$PACKAGE_DIR/opt/breakingbadhabits"
mkdir -p "$PACKAGE_DIR/usr/bin"
mkdir -p "$PACKAGE_DIR/usr/share/applications"

# 2. Create control file (Added python3-gi and gtk dependencies)
cat <<EOF > "$PACKAGE_DIR/DEBIAN/control"
Package: ${APP_NAME}
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: amd64
Maintainer: Breaking Bad Habits Team
Depends: python3, policykit-1, python3-pil, python3-tk, python3-gi, gir1.2-gtk-3.0, gir1.2-ayatanaappindicator3-0.1, libevdev2
Description: A robust tool to help break bad habits and track progress.
 Enforces domain blocking via hosts file and monitors activity for workout reminders.
EOF

# 3. Copy application files
cp -r src "$PACKAGE_DIR/opt/breakingbadhabits/"
cp launch.sh "$PACKAGE_DIR/opt/breakingbadhabits/"
cp open_dashboard.sh "$PACKAGE_DIR/opt/breakingbadhabits/"
cp requirements.txt "$PACKAGE_DIR/opt/breakingbadhabits/"
cp BreakingBadHabits.desktop "$PACKAGE_DIR/usr/share/applications/breakingbadhabits.desktop"

# 4. Create the global executable link
ln -s "/opt/breakingbadhabits/launch.sh" "$PACKAGE_DIR/usr/bin/breakingbadhabits"

# 5. Build and Package the Virtual Environment (Self-Contained)
echo "Building portable virtual environment..."
# Create venv inside the build directory
python3 -m venv --system-site-packages "$PACKAGE_DIR/opt/breakingbadhabits/venv"

# Install requirements into the package's venv
"$PACKAGE_DIR/opt/breakingbadhabits/venv/bin/pip" install --upgrade pip
"$PACKAGE_DIR/opt/breakingbadhabits/venv/bin/pip" install -r requirements.txt

# CRITICAL: Fix shebangs to point to the FINAL destination on the target machine
# Even though we build it here, the scripts must think they live in /opt/breakingbadhabits/
echo "Fixing venv portability..."
find "$PACKAGE_DIR/opt/breakingbadhabits/venv/bin" -type f -executable -exec sed -i '1s|^#!.*python.*|#!/opt/breakingbadhabits/venv/bin/python|' {} +

# 6. Create a clean post-install script (No network/build required)
cat <<EOF > "$PACKAGE_DIR/DEBIAN/postinst"
#!/bin/bash
set -e
echo "Finalizing Breaking Bad Habits installation..."

# Fix permissions for the app directory
chown -R root:root /opt/breakingbadhabits
chmod -R 755 /opt/breakingbadhabits

# Ensure scripts are executable
chmod +x /opt/breakingbadhabits/launch.sh
chmod +x /opt/breakingbadhabits/open_dashboard.sh

echo "Installation successful! You can start the app with 'breakingbadhabits' or from your application menu."
EOF
chmod 755 "$PACKAGE_DIR/DEBIAN/postinst"

# 7. Build the package
dpkg-deb --build "$PACKAGE_DIR"

echo "------------------------------------------------"
echo "Done! Your package is at: ${PACKAGE_DIR}.deb"
echo "------------------------------------------------"
