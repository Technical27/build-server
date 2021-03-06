{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = [
    (pkgs.python3.withPackages (ps: with ps; [
      PyGithub
      python-dotenv
      pygit2
      pyjwt
      setuptools
      requests
      python-language-server
    ]))
  ];
}
