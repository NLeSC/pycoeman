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
          'numpy', 'tabulate', 'matplotlib', 'lxml', 'pandas'
    ],
)
