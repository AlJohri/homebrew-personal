class Kar < Formula
  desc "Kar"
  url "https://github.com/AlJohri/kar.git", :using => GitDownloadStrategy
  version "0.0.1"

  def install
    bin.install "kar"
  end
end