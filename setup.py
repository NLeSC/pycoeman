from distutils.core import setup

setup(
    name='pycoeman',
    version='0.1dev',
    packages=['pycoeman', 'pycoeman.seqcommands', 'pycoeman.parcommands', 'pycoeman.monitor',],
    license='Apache License 2.0',
    long_description=open('README.md').read(),
    author='Oscar Martinez-Rubi',
    author_email='o.rubi@esciencecenter.nl',
    url='https://github.com/oscarmartinezrubi/pycoeman',
    install_requires=[
          'numpy', 'tabulate', 'matplotlib', 'lxml', 'pandas', 'paramiko', 'scp'
    ],
    entry_points={
        'console_scripts': [
            'coeman-seq-local=pycoeman.seqcommands.run_seqcommands_local:main',
            'coeman-par-local=pycoeman.parcommands.run_parcommands_local:main',
            'coeman-par-ssh=pycoeman.parcommands.run_parcommands_ssh:main',
            'coeman-par-sge=pycoeman.parcommands.run_parcommands_sge_cluster.create_parcommands_sge_jobs:main',
        ],
    },
)
