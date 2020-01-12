class Kar < Formula
  desc "Kar"
  url "https://github.com/AlJohri/kar.git", :using => GitDownloadStrategy
  version "0.0.2"
  depends_on "bash" # for bash associative arrays
  depends_on "coreutils" # for realpath

  def install
    libexec.install "kar", "help.sh"
    bin.install_symlink "#{libexec}/kar"
  end
end
