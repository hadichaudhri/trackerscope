export default function Cookie() {
    return (
        <>
            <h1>Cookie</h1>
            <p>
                Cookie is a small piece of data stored on the user&apos;s
                computer by the web browser while browsing a website. Cookies
                were designed to be a reliable mechanism for websites to
                remember stateful information or to record the user&apos;s
                browsing activity.
            </p>
        </>
    );
}

export const getServerSideProps = async (context) => {
    context.res.setHeader("Set-Cookie", "tracking=true");
    return { props: {} };
};
