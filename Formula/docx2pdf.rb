class Docx2pdf < Formula
  include Language::Python::Virtualenv

  desc "Convert docx2 to pdf"
  homepage "https://github.com/AlJohri/docx2pdf"
  url "https://files.pythonhosted.org/packages/15/b5/813dccfc3e0d86312b1fc1183e1062b2f14add314e1235fd7a54d80bfe83/docx2pdf-0.1.4.tar.gz"
  sha256 "c3c1e19806d9a4fb3772d6a3e78d3efdaa12a790d2aef5948203890475834b13"
  head "https://github.com/AlJohri/docx2pdf.git"

  depends_on "python"

  resource "appscript" do
    url "https://files.pythonhosted.org/packages/40/66/a50e927ec8d999b3c9fd0d93e7ea5413e38671343d0ce6d509fdaf0e53c0/appscript-1.1.0.tar.gz"
    sha256 "35c2ba2894348413a29daa19008d5f1c349a832206eccc97ded50cee3ad852e5"
  end

  resource "importlib-metadata" do
    url "https://files.pythonhosted.org/packages/cb/bb/7a935a48bf751af244090a7bd558769942cf13a7eba874b8b25538f3db01/importlib_metadata-1.3.0.tar.gz"
    sha256 "073a852570f92da5f744a3472af1b61e28e9f78ccf0c9117658dc32b15de7b45"
  end

  resource "more-itertools" do
    url "https://files.pythonhosted.org/packages/4e/b2/e9e512cccde6c54bf66a8e5820a2af779eb8235028627002ca90d4f75bea/more-itertools-8.0.2.tar.gz"
    sha256 "b84b238cce0d9adad5ed87e745778d20a3f8487d0f0cb8b8a586816c7496458d"
  end

  resource "tqdm" do
    url "https://files.pythonhosted.org/packages/cc/84/6005c80747390ca4355d0f0ec416068a46f26eed4ea6029660c71e87ccd4/tqdm-4.41.0.tar.gz"
    sha256 "166a82cdea964ae45528e0cc89436255ff2be73dc848bdf239f13c501cae5dc7"
  end

  resource "zipp" do
    url "https://files.pythonhosted.org/packages/57/dd/585d728479d97d25aeeb9aa470d36a4ad8d0ba5610f84e14770128ce6ff7/zipp-0.6.0.tar.gz"
    sha256 "3718b1cbcd963c7d4c5511a8240812904164b7f381b647143a89d3b98f9bcd8e"
  end

  def install
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

  test do
    system "false"
  end
end
