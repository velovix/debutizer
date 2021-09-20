#!/usr/bin/env bash

set -o errexit
set -o pipefail
set -o nounset

locales=("en_US")

function update_translations {
  domain=$1
  input_paths=$2

  pybabel extract \
    --output "locale/${domain}.pot" \
    --no-location \
    --copyright-holder "Tyler Compton <xaviosx@gmail.com>" \
    --project debutizer \
    --keyword tr \
    ${input_paths}

  for locale in "${locales[@]}"; do
    if [[ -f "locale/${locale}/LC_MESSAGES/${domain}.po" ]]; then
      pybabel update \
        --locale "${locale}" \
        --input-file "locale/${domain}.pot" \
        --output-dir locale \
        --domain "${domain}" \
        --ignore-obsolete
    else
      pybabel init \
        --locale "${locale}" \
        --input-file "locale/${domain}.pot" \
        --output-dir locale \
        --domain "${domain}"
    fi
  done

  pybabel compile \
    --directory locale \
    --domain "${domain}"
}

update_translations portal debutizer/__main__.py
update_translations build_command debutizer/commands/build.py
update_translations general debutizer/configuration.py
