const Footer = () => {
  return (
    <footer className="bg-primary flex w-full p-5 items-center justify-between text-primary-foreground">
      <div className="w-full">
        <p className="text-sm">
          Source code available on{" "}
          <a
            href="https://github.com/ShadowChaser4/dns-tools"
            target="_blank"
            rel="noopener noreferrer"
            className="underline hover:text-primary-foreground/80"
          >
            GitHub
          </a>
        </p>
        <p className="text-xs">
          &copy; {new Date().getFullYear()} DNS Tools. All rights reserved.
        </p>
      </div>
      <div className="w-full flex items-center justify-end">
        <p className="text-xs">
          Made with ❤️ by{" "}
          <a
            href="https://github.com/ShadowChaser4"
            target="_blank"
            rel="noopener noreferrer"
            className="underline"
          >
            Kushal
          </a>
        </p>
      </div>
    </footer>
  );
};

export default Footer;
