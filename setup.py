from setuptools import setup, find_packages

setup(
    name                    = 'dynamicargparse',
    version                 = '1.01',
    description             = 'Python Dynamic Argument Parser',
    author                  = 'Jeonghyun Joo',
    author_email            = 'jhjoo.root@gmail.com',
    packages                = ['.'],
    url                     = 'https://github.com/JeonghyunJoo/dynamic-arg-parser',
    download_url            = 'https://github.com/JeonghyunJoo/archive/1.0.tar.gz',
    install_requires        = ['PyYAML>=5.1'],
    python_requires         = '>=3.5',
    classifiers             = [
                                'Programming Language :: Python :: 3.5',
                                'Programming Language :: Python :: 3.6',
                                'Programming Language :: Python :: 3.7',
                                'Programming Language :: Python :: 3.8',
                            ]
    )
