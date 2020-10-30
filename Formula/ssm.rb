class Ssm < Formula
    desc "SSM"
    url "https://github.com/AlJohri/homebrew--.git", :using => GitDownloadStrategy
    version "0.0.1"
    depends_on "awscli"
  
    def install
        Dir.chdir('tools/ssm')
        xy = Language::Python.major_minor_version "python3"
        ENV.prepend_create_path "PYTHONPATH", libexec/"vendor/lib/python#{xy}/site-packages"
        resources.each do |r|
          r.stage do
            system "python3", *Language::Python.setup_install_args(libexec/"vendor")
          end
        end
        ENV.prepend_create_path "PYTHONPATH", libexec/"lib/python#{xy}/site-packages"
        system "python3", *Language::Python.setup_install_args(libexec)
        bin.install Dir[libexec/"bin/*"]
        bin.env_script_all_files(libexec/"bin", :PYTHONPATH => ENV["PYTHONPATH"])
      end
  end
  