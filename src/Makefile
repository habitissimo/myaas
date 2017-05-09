test=''
CWD:= $(shell pwd)
HOSTNAME := $(shell hostname -i)
IMAGE=habitissimo/myaas
DOCKER_RUN_FLAGS = --rm -e "HOST_NAME=$(HOSTNAME)"
run     : DOCKER_RUN_FLAGS += -p 5001:80 --name=dbm-server
dev     : DOCKER_RUN_FLAGS += -p 5001:80 -v "$(PWD):/code" -e "DEBUG=True" --name=myaas-server-dev
daemon  : DOCKER_RUN_FLAGS += -it --name=myaas-daemon
daemon-dev: DOCKER_RUN_FLAGS += -it --name=myaas-daemon -v "$(PWD):/code" -e "DEBUG=True"
shell   : DOCKER_RUN_FLAGS += -it -v "$(PWD):/code" --entrypoint=ipython --name=myaas-ipython
bash    : DOCKER_RUN_FLAGS += -it -v "$(PWD):/code" --entrypoint=bash --name=myaas-bash
flake   : DOCKER_RUN_FLAGS += -it -v "$(PWD):/code" --name=myaas-flake8
tests   : DOCKER_RUN_FLAGS += -it -v "$(PWD):/code" --name=myaas-nosetest
update  : DOCKER_RUN_FLAGS += -t --name=myaas-update
DOCKER_RUN=docker run $(DOCKER_RUN_FLAGS) \
	-v /var/run/docker.sock:/var/run/docker.sock \
	-v /opt/myaas:/myaas \
	$(IMAGE)

# build the image
build:
	docker build -t $(IMAGE) .

# push the image to the docker registry
push:
	docker push $(IMAGE)

# run the daemon
daemon:
	$(DOCKER_RUN) daemon

# run the daemon
daemon-dev:
	$(DOCKER_RUN) daemon

# run the image
run: build
	$(DOCKER_RUN)

# run the image in development mode
dev:
	$(DOCKER_RUN) python runserver.py

# run the update task (find templates and import them)
update: build
	${DOCKER_RUN} update

# check pep8
pep: flake
flake:
	-@PAGER=cat git grep -i myass -- './*' ':(exclude)Makefile'  && echo "####\nWarning myASS typo detected!\n####"
	@${DOCKER_RUN} flake8 --ignore=E501,F841 .

# run the test suite
test: tests
tests: flake
	${DOCKER_RUN} nosetests -v -x --rednose --pdb $(test)

# open an ipython shell for testing
shell:
	${DOCKER_RUN}

# opens a shell inside the container for testing
bash:
	${DOCKER_RUN}

.PHONY: build push run dev update test tests shell
