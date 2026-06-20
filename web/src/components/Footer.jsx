export default function Footer({ sponsor }) {
  return (
    <footer className="footer">
      <div className="footer__rule" />
      <p className="footer__submit">
        To submit an obituary, email it with a photo to{" "}
        <a href="mailto:editor@wausaupilotandreview.com">
          editor@wausaupilotandreview.com
        </a>
        , or ask your funeral home for assistance. There is no charge.
      </p>
      {sponsor?.name && (
        <p className="footer__sponsor">
          Obituary coverage on Wausau Pilot &amp; Review is sponsored by{" "}
          {sponsor.name}.
        </p>
      )}
    </footer>
  );
}
