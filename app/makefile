SHELL = /bin/bash

project_dependencies ?= $(addprefix $(project_root)/, \
		emissor \
		cltl-combot \
		cltl-context \
		cltl-requirements \
		cltl-emissor-data \
		cltl-chat-ui \
		cltl-knowledgeextraction \
		cltl-knowledgelinking \
		cltl-knowledgerepresentation \
		cltl-languagegeneration \
		cltl-dialogueclassification \
		cltl-emotionrecognition \
		cltl-about-agent \
		app)

git_remote ?= https://github.com/leolani

include util/make/makefile.base.mk
include util/make/makefile.component.mk
include util/make/makefile.py.base.mk
include util/make/makefile.git.mk

spacy.lock: venv
	test -e spacy.lock || (source venv/bin/activate; python -m spacy download en)
	test -e spacy.lock || (source venv/bin/activate; python -m spacy download nl)
	touch spacy.lock

nltk.lock: venv
	test -e nltk.lock || (source venv/bin/activate; python -m nltk.downloader -d ~/nltk_data all)
	touch nltk.lock

ollama.lock: venv
	test -e ollama.lock || (source venv/bin/activate; ollama pull llama3.2:1b)
	#test -e ollama.lock || (source venv/bin/activate; ollama pull llama3.2)
	touch ollama.lock

py-app/resources/midas-da-xlmroberta/models.lock:
	mkdir -p py-app/resources/midas-da-xlmroberta
	wget "https://vu.data.surfsara.nl/index.php/s/dw0YCJAVFM870DT/download" -O py-app/resources/midas-da-xlmroberta/models.zip
	unzip -j -d py-app/resources/midas-da-xlmroberta py-app/resources/midas-da-xlmroberta/models.zip
	rm py-app/resources/midas-da-xlmroberta/models.zip
	touch py-app/resources/midas-da-xlmroberta/models.lock

py-app/resources/conversational_triples/models.lock:
	mkdir -p py-app/resources/conversational_triples
	wget "https://vu.data.surfsara.nl/index.php/s/Ib6OcZHpfUyB5fm/download" -O py-app/resources/conversational_triples/argument_extraction_bert-base-multilingual-cased.pt
	wget "https://vu.data.surfsara.nl/index.php/s/LKTkoSZZpflaIaw/download" -O py-app/resources/conversational_triples/candidate_scorer_bert-base-multilingual-cased.pt
	wget "https://vu.data.surfsara.nl/index.php/s/WpL1vFChlQpkbqW/download" -O py-app/resources/conversational_triples/models.zip
	unzip -j -d py-app/resources/conversational_triples py-app/resources/conversational_triples/models.zip
	rm py-app/resources/conversational_triples/models.zip
	touch py-app/resources/conversational_triples/models.lock


.PHONY: build
build: venv \
	nltk.lock spacy.lock \
	py-app/resources/conversational_triples/models.lock \
	py-app/resources/midas-da-xlmroberta/models.lock


.PHONY: clean
clean: py-clean base-clean
	rm -f spacy.lock nltk.lock ollama.lock
	rm -rf py-app/resources/conversational_triples
	rm -rf py-app/resources/midas-da-xlmroberta/


.PHONY: generate
generate:
	docker run --rm -v "${PWD}/src/hitep_generated:/local" openapitools/openapi-generator-cli generate \
		-g python-flask \
		-i https://raw.githubusercontent.com/hi-tep/tep-rest-api/refs/heads/main/leolani-tep-api.yaml \
		-o /local


# .PHONY: generate
# generate:
# 	docker run --rm -v "${PWD}/src:/local" openapitools/openapi-generator-cli generate --skip-overwrite \
# 		-g python-flask --additional-properties=packageName=hitep_service.rest.openapi \
# 		-i https://raw.githubusercontent.com/hi-tep/tep-rest-api/refs/heads/main/leolani-tep-api.yaml \
# 		-o /local
