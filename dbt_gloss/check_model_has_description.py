import argparse
import os
from distutils.log import debug
from typing import Any
from typing import Dict
from typing import Optional
from typing import Sequence

from dbt_gloss.utils import add_filenames_args
from dbt_gloss.utils import add_manifest_args
from dbt_gloss.utils import get_filenames
from dbt_gloss.utils import get_json
from dbt_gloss.utils import get_model_schemas
from dbt_gloss.utils import get_model_sqls
from dbt_gloss.utils import get_models
from dbt_gloss.utils import JsonOpenError

from dbt_gloss.tracking import dbtGlossTracking


def has_description(paths: Sequence[str], manifest: Dict[str, Any]) -> int:
    status_code = 0
    ymls = get_filenames(paths, [".yml", ".yaml"])
    sqls = get_model_sqls(paths, manifest)
    filenames = set(sqls.keys())

    # get manifest nodes that pre-commit found as changed
    models = get_models(manifest, filenames)
    # if user added schema but did not rerun the model
    schemas = get_model_schemas(list(ymls.values()), filenames)
    # convert to sets
    in_models = {model.filename for model in models if model.node.get("description")}
    in_schemas = {
        schema.model_name for schema in schemas if schema.schema.get("description")
    }
    missing = filenames.difference(in_models, in_schemas)
    error_msg_list = []
    for model in missing:
        status_code = 1
        error_msg = f"{sqls.get(model)}:" \
                    f" does not have defined description or properties file is missing."
        error_msg_list.append(error_msg)
        print(error_msg)

    mixpanel = dbtGlossTracking()
    mixpanel.track_hook_event(
        hook_name=os.path.basename(__file__),
        hook_properties={
            'Description': 'Check the model has description',
            'Status': status_code,
            'Error Messages': error_msg_list
        },
        manifest=manifest
    )

    return status_code


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    add_filenames_args(parser)
    add_manifest_args(parser)

    args = parser.parse_args(argv)

    try:
        manifest = get_json(args.manifest)
    except JsonOpenError as e:
        print(f"Unable to load manifest file ({e})")
        return 1

    return has_description(paths=args.filenames, manifest=manifest)


if __name__ == "__main__":
    exit(main())
