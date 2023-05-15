# Unit Testing

## Details
Unit tests are currently setup to use [Pytest](https://docs.pytest.org/en/7.3.x/contents.html).

## Setup

Setting up an environment for testing is quite simple.

From a clean Linux image you run the following commands, and you'll be all set.

1. Download the Sarracenia source  
  `git clone https://github.com/MetPX/sarracenia`
2. Checkout the branch you're working on (optional)  
  `git checkout <BranchName>`
3. Update PIP  
  `pip3 install -U pip`
4. Install base requirements for Sarracenia  
  `pip install -r requirements.txt`
5. Install sarracenia Python modules  
  `pip3 install -e .`
6. Install requirements for PyTest  
  `pip install -r tests/requirements.txt`

That's it, you're now ready to run the tests.

## Running

From within the repository root directory, simply run `pytest tests` and you'll see the results. There's a full set of arguments/options that modify the output, outlined [here](https://docs.pytest.org/en/7.3.x/reference/reference.html#ini-options-ref).  

As configured, it will output a bit of system information, total tests, followed by a line per file, with dots/letters  to indicate the status of each test in that file.  
Letter meanings: 
(`f`)ailed, (`E`)rror, (`s`)kipped, (`x`)failed, (`X`)passed, (`p`)assed, (`P`)assed with output, (`a`)ll except passed (`p`/`P`), (`w`)arnings, (`A`)ll

Specifying the `-v` option will make it a bit more verbose, listing each tests, and it's pass/skip/fail status.  

Application logs captured during tests can be output with the `-o log_cli=true` argument.


## Docker
You can also run the exact same tests from within a Docker container if you want to avoid having to (re)-provision clean installs.

If the code is already present on the host system, you can use the `python` image, and map the code into the container for the tests:  
`docker run --rm -it --name sr3-pytest -v $(pwd):/app -w /app python:3 bash`

Then you run the Setup section above, starting at Step 3.

If the code isn't already on your system, then the following should get you setup:
- Run container  
  `docker run --rm -it --name sr3-pytest ubuntu bash`
- Install dependencies (Ubuntu/Debian)  
  `apt-get update && apt-get install -y git python3 python3-pip`
- Then follow the Setup directions above