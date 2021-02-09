{ python3Packages }:

python3Packages.buildPythonPackage {
  pname = "build-server";
  version = "0.0.0";

  src = ./.;

  propagatedBuildInputs = with python3Packages; [ pygit2 PyGithub python-dotenv ];

  doCheck = false;
}
