name: Generate Snake Animation

on:
  schedule:
    - cron: "0 0 * * *"   # runs once a day
  workflow_dispatch: {}   # lets you trigger it manually from the Actions tab
  push:
    branches:
      - main

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - name: Generate snake animation
        uses: Platane/snk@v3
        with:
          github_user_name: vinitsoni03
          outputs: |
            dist/github-contribution-grid-snake-dark.svg?palette=github-dark
            dist/github-contribution-grid-snake.svg

      - name: Push snake svg to output branch
        uses: crazy-max/ghaction-github-pages@v4
        with:
          target_branch: output
          build_dir: dist
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
