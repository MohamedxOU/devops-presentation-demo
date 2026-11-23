// Chaîne CI/CD de la démo M354
// Toutes les branches : intégration continue (lint, tests, sécurité, build, scan).
// Branche main uniquement : release, staging, approbation humaine, production.

pipeline {
  agent any

  options {
    timestamps()
    disableConcurrentBuilds()
    buildDiscarder(logRotator(numToKeepStr: '20'))
  }

  environment {
    IMAGE   = "${env.DOCKER_IMAGE ?: 'm354-planning'}"
    VERSION = "1.0.${env.BUILD_NUMBER}"
  }

  stages {

    stage('Plan · carte Trello') {
      steps {
        script {
          env.TRELLO_CARD = sh(returnStdout: true, script: 'python3 scripts/trello.py card-from-commit').trim()
          env.SHORT_SHA   = sh(returnStdout: true, script: 'git rev-parse --short HEAD').trim()
          currentBuild.displayName = "#${env.BUILD_NUMBER} ${env.SHORT_SHA}"
          echo env.TRELLO_CARD ? "Carte Trello liée : ${env.TRELLO_CARD}" : 'Aucune carte Trello citée dans le commit'
        }
      }
    }

    stage('Code · dépendances') {
      steps {
        sh '''
          python3 -m venv .venv
          . .venv/bin/activate
          pip install -q --upgrade pip
          pip install -q -r requirements-dev.txt
          mkdir -p reports
        '''
      }
    }

    stage('Test · lint') {
      steps {
        sh '. .venv/bin/activate && ruff check . && ruff format --check .'
      }
    }

    stage('Test · unitaires') {
      steps {
        sh '''
          . .venv/bin/activate
          pytest --junitxml=reports/junit.xml \
                 --cov --cov-report=xml:reports/coverage.xml --cov-report=term \
                 --cov-fail-under=80
        '''
      }
      post {
        always {
          junit 'reports/junit.xml'
          recordCoverage(tools: [[parser: 'COBERTURA', pattern: 'reports/coverage.xml']],
                         id: 'coverage', name: 'Couverture des tests')
        }
      }
    }

    stage('Test · sécurité du code') {
      parallel {
        stage('SAST (Bandit)') {
          steps {
            sh '. .venv/bin/activate && bandit -r app -c pyproject.toml -f txt -o reports/bandit.txt; status=$?; cat reports/bandit.txt; exit $status'
          }
        }
        stage('Dépendances (pip-audit)') {
          steps {
            sh '. .venv/bin/activate && pip-audit -r requirements.txt'
          }
        }
      }
    }

    stage('Build · image Docker') {
      steps {
        sh '''
          docker build \
            --build-arg APP_VERSION="$VERSION" \
            --build-arg GIT_COMMIT="$SHORT_SHA" \
            -t "$IMAGE:$SHORT_SHA" .
        '''
      }
    }

    stage('Test · scan image (Trivy)') {
      steps {
        sh '''
          docker run --rm \
            -v /var/run/docker.sock:/var/run/docker.sock \
            -v trivy-cache:/root/.cache \
            aquasec/trivy:0.76.2 image \
              --scanners vuln --ignore-unfixed \
              --severity CRITICAL --exit-code 1 \
              "$IMAGE:$SHORT_SHA"
        '''
      }
    }

    stage('Test · conteneur') {
      steps {
        sh '''
          docker rm -f "ci-$SHORT_SHA" >/dev/null 2>&1 || true
          docker run -d --name "ci-$SHORT_SHA" --network devops-demo "$IMAGE:$SHORT_SHA"
          ./scripts/smoke.sh "ci-$SHORT_SHA" "$VERSION"
        '''
      }
      post {
        always {
          sh 'docker rm -f "ci-$SHORT_SHA" >/dev/null 2>&1 || true'
        }
      }
    }

    stage('Release · Docker Hub') {
      when { branch 'main' }
      steps {
        withCredentials([usernamePassword(credentialsId: 'dockerhub',
                                          usernameVariable: 'DH_USER',
                                          passwordVariable: 'DH_TOKEN')]) {
          sh '''
            docker tag "$IMAGE:$SHORT_SHA" "$IMAGE:$VERSION"
            docker tag "$IMAGE:$SHORT_SHA" "$IMAGE:latest"
            if [ -n "$DH_USER" ] && [ -n "$DH_TOKEN" ]; then
              echo "$DH_TOKEN" | docker login -u "$DH_USER" --password-stdin
              docker push "$IMAGE:$VERSION"
              docker push "$IMAGE:$SHORT_SHA"
              docker push "$IMAGE:latest"
              docker logout
            else
              echo "Docker Hub non configuré : image gardée dans le registre local du poste."
            fi
          '''
        }
        sh '''
          {
            echo "# Release v$VERSION"
            echo
            echo "- Image : $IMAGE:$VERSION"
            echo "- Commit : $SHORT_SHA"
            echo
            echo "## Changements"
            git log -5 --pretty='- %s (%h)'
          } > RELEASE.md
          cat RELEASE.md
        '''
        archiveArtifacts artifacts: 'RELEASE.md', fingerprint: true
        script { currentBuild.description = "v${env.VERSION}" }
      }
    }

    stage('Deploy · staging') {
      when { branch 'main' }
      steps {
        sh '''
          ./scripts/deploy.sh staging "$IMAGE:$VERSION"
          ./scripts/smoke.sh app-staging "$VERSION"
        '''
      }
    }

    stage('Deploy · approbation') {
      when { branch 'main' }
      steps {
        timeout(time: 15, unit: 'MINUTES') {
          input message: "Déployer v${env.VERSION} en production ?", ok: 'Déployer'
        }
      }
    }

    stage('Deploy · production') {
      when { branch 'main' }
      steps {
        sh '''
          ./scripts/deploy.sh production "$IMAGE:$VERSION"
          ./scripts/smoke.sh app-production "$VERSION"
        '''
      }
    }

    stage('Operate · retour Trello') {
      when { branch 'main' }
      steps {
        withCredentials([string(credentialsId: 'trello-key', variable: 'TRELLO_KEY'),
                         string(credentialsId: 'trello-token', variable: 'TRELLO_TOKEN')]) {
          sh '''
            if [ -n "$TRELLO_CARD" ]; then
              python3 scripts/trello.py comment "$TRELLO_CARD" "En production : v$VERSION (commit $SHORT_SHA). Build : $BUILD_URL"
              python3 scripts/trello.py move "$TRELLO_CARD" "${TRELLO_LIST_DONE:-}"
            fi
          '''
        }
      }
    }
  }

  post {
    success {
      script {
        if (env.BRANCH_NAME != 'main' && env.TRELLO_CARD) {
          withCredentials([string(credentialsId: 'trello-key', variable: 'TRELLO_KEY'),
                           string(credentialsId: 'trello-token', variable: 'TRELLO_TOKEN')]) {
            sh 'python3 scripts/trello.py comment "$TRELLO_CARD" "CI verte sur la branche $BRANCH_NAME ($SHORT_SHA). Build : $BUILD_URL"'
          }
        }
      }
    }
    failure {
      withCredentials([string(credentialsId: 'trello-key', variable: 'TRELLO_KEY'),
                       string(credentialsId: 'trello-token', variable: 'TRELLO_TOKEN')]) {
        sh '''
          if [ -n "${TRELLO_CARD:-}" ]; then
            python3 scripts/trello.py comment "$TRELLO_CARD" "Pipeline ROUGE sur $BRANCH_NAME ($SHORT_SHA) : rien n'est parti en production. $BUILD_URL"
          fi
          if [ "$BRANCH_NAME" = "main" ]; then
            python3 scripts/trello.py create "${TRELLO_LIST_TODO:-}" "Pipeline main en échec (build $BUILD_NUMBER)" "$BUILD_URL"
          fi
        '''
      }
    }
  }
}
