class OutlookAppleCalendarSync < Formula
  desc "Kar"
  url "https://github.com/AlJohri/outlook-apple-calendar-sync.git", :using => GitDownloadStrategy
  version "0.0.1"

  def install
  	mv "sync.jxa", "outlook-apple-calendar-sync"
    bin.install "outlook-apple-calendar-sync"
  end

  def plist; <<~EOS
    <?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
    <plist version="1.0">
    <dict>
      <key>KeepAlive</key>
      <dict>
        <key>SuccessfulExit</key>
        <false/>
      </dict>
      <key>Label</key>
      <string>#{plist_name}</string>
      <key>ProgramArguments</key>
      <array>
        <string>#{opt_bin}/#{name}</string>
      </array>
      <key>RunAtLoad</key>
      <true/>
      <key>WorkingDirectory</key>
      <string>#{HOMEBREW_PREFIX}</string>
      <key>StandardOutPath</key>
      <string>#{var}/log/#{name}.log</string>
      <key>StandardErrorPath</key>
      <string>#{var}/log/#{name}.log</string>
      <key>StartInterval</key>
      <integer>600</integer>
    </dict>
    </plist>
  EOS
  end

end
