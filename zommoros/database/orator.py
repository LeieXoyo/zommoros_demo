from zommoros import project_dir

DATABASES = {
    'sqlite': {
        'driver': 'sqlite',
        'database': f'{project_dir}/database/mystic_forge.db'
    }
}
