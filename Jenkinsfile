#!groovy

PROJECT_NAME = "maf-lib"
PYENV_VERSION = "3.6-dev"

BRANCH_NAME = env.BRANCH_NAME
GIT_HASH = ""
VERSION = ""

PROXY = "http://cloud-proxy:3128"

pipeline {
  agent any
  environment {
        TWINE_REPOSITORY_URL = credentials("${BRANCH_NAME == 'master' ? 'twine_repository_url_prod' : 'twine_repository_url'}")
	TWINE_USERNAME = credentials('twine_username')
	TWINE_PASSWORD = credentials('twine_password')
	QUAY_USERNAME = credentials('QUAY_USERNAME')
	QUAY_PASSWORD = credentials('QUAY_PASSWORD')
  }
  options {
    disableConcurrentBuilds()
    skipStagesAfterUnstable()
  }

  stages {
    stage('Init') {
      steps {
        vbash 'make version'

	script {
	  GIT_HASH = sh(script: 'git rev-parse HEAD', returnStdout: true).trim()
	  VERSION = sh(script: "make print-version BRANCH_NAME=${BRANCH_NAME}", returnStdout: true).trim()
	  PYPI_VERSION = sh(script: "make print-pypi", returnStdout: true).trim()
	  currentBuild.displayName = "#${currentBuild.number} - ${VERSION}"
	}

	echo "Version: ${VERSION}"
      }
    }
    stage('Docker Build') {
      steps {
        vbash "make build-docker PROXY=${PROXY}"
      }
    }
    stage('Docker Test') {
      steps {
        sh 'make test-docker'
      }
    }
    stage('Docker Publish Staging') {
      when {
        anyOf {
	  branch 'feat/*'
	  branch 'develop'
	  branch 'feature/*'
	  branch 'hotfix/*'
	  branch 'release/*'
	}
      }
      steps {
        sh 'make publish-staging'
      }
    }
    stage('Docker Publish Release') {
      when {
        anyOf {
	  branch 'master'
	}
      }
      steps {
        sh 'make publish-release'
      }
    }
    stage('PyPI Publish') {
      when { 
        anyOf {
	  branch 'master'
	  branch 'develop'
	  branch 'hotfix/*'
	  branch 'release/*'
	}
      }
      steps {
	echo "Building PyPI Version: ${PYPI_VERSION}"
        sh "pip install --user twine wheel"
        vbash "make build-pypi"
        vbash "make publish-pypi"
      }
    }
  }
}

def vbash(command) {
  sh """#!/bin/bash
        eval \"\$(pyenv init -)\"
	eval \"\$(pyenv virtualenv-init -)\"

	pyenv virtualenv ${PYENV_VERSION} ${PROJECT_NAME}-venv || true
	pyenv activate ${PROJECT_NAME}-venv

	${command}
  """
}
