import { useEffect, useState } from "react";

export default function Tracked({ cookie }) {
    // // Store a cookie on the user's computer
    // const cookieStore = await cookies();
    // const cookie = cookieStore.set("userID", "1234");
    const [localStorageFound, setLocalStorageFound] = useState("False");

    useEffect(() => {
        if (localStorage.getItem("userID")) {
            setLocalStorageFound("True");
        }
    });

    return (
        <>
            <h1>Am I being tracked?</h1>
            <div>Cookies found: {cookie}</div>
            <div>Local storage found: {localStorageFound}</div>
        </>
    );
}

export const getServerSideProps = async (context) => {
    // If we've seen this person before, display a "Welcome back!" message
    const tracking = context.req.cookies.tracking;
    if (tracking === "true") {
        return { props: { cookie: "True" } };
    }
    return { props: { cookie: "False" } };
};
