build_deb:
	docker pull $(DISTRO)
	docker build -t screamshotter_deb -f ./Dockerfile.debian.builder --build-arg DISTRO=$(DISTRO) .
	docker run --name screamshotter_deb_run -t screamshotter_deb bash -c "exit"
	docker cp screamshotter_deb_run:/dpkg ./
	docker stop screamshotter_deb_run
	docker rm screamshotter_deb_run