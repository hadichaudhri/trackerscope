import Link from "next/link";

export default function Home() {
    return (
        <>
            <div>
                <Link href="/cookie">Cookie</Link>
            </div>
            <div>
                <Link href="/storage">Local Storage</Link>
            </div>
            <div>
                <Link href="/fingerprint">Fingerprint</Link>
            </div>
            <div>
                <Link href="/tracked">Am I Being Tracked?</Link>
            </div>
        </>
    );
}
