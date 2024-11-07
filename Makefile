.PHONY: release shasum clean

VERSION := $(shell python setup.py --version)
DIST_PATH := dist
APP_NAME := gorunn
RELEASE_NOTES := "Stable release version $(VERSION)"

# Clean old builds
clean:
	rm -fr build/ dist/
# Build the package distribution
build: clean
	python setup.py sdist bdist_wheel

# Create SHA sum file
shasum: build
	shasum -a 256 $(DIST_PATH)/* > $(DIST_PATH)/SHA256SUMS

# Create a release on GitHub
release: build
	git tag $(VERSION) && \
	git push origin main && \
	git push origin $(VERSION) && \
	gh release create $(VERSION) $(DIST_PATH)/* --notes $(RELEASE_NOTES)

# Publish to PyPi
publish:
	twine upload $(DIST_PATH)/*

# Full release process
full_release: build release publish
