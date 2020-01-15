class Kar < Formula
  desc "Kar"
  url "https://github.com/AlJohri/kar.git", :using => GitDownloadStrategy
  version "0.0.3"
  depends_on "bash" # for bash associative arrays
  depends_on "coreutils" # for realpath

  def install
    libexec.install "kar", "kar.sh", "kar.py", "help.sh"
    bin.install_symlink "#{libexec}/kar"
  end
end
