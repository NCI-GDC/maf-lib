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
        TWINE_REPOSITORY_URL = credentials("${BRANCH_NAME == 'main' ? 'twine_repository_url_prod' : 'twine_repository_url'}")
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
          PYPI_VERSION = sh(script: "make print-pypi", returnStdout: true).trim()
          currentBuild.displayName = "#${currentBuild.number} - ${PYPI_VERSION}"
        }
      }
    }
    stage('Tox') {
      steps {
        vbash "make tox"
      }
    }
    stage('PyPI Publish Branch') {
      when { 
        anyOf {
          branch 'main'
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
