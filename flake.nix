{
  description = "build server";

  outputs = { self, nixpkgs }: let
    pkgs = nixpkgs.legacyPackages.x86_64-linux;
  in {
    devShell.x86_64-linux = import ./shell.nix { inherit pkgs; };
    defaultPackage.x86_64-linux = pkgs.callPackage ./default.nix {};
  };
}
