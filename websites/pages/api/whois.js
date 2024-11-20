import whois from "whois-json";

export default async (req, res) => {
    try {
        // const { ip } = req.query;
        const ip = req.query.ip;

        // Validate IP
        if (!ip || !isValidIP(ip)) {
            return res.status(400).json({ error: "Invalid IP address" });
        }

        // Perform WHOIS lookup
        const whoisData = await whois(ip);
        return res.status(200).json(whoisData);
    } catch (err) {
        console.error("Error in WHOIS handler:", err);
        return res.status(500).json({ error: "Internal Server Error" });
    }
};

function isValidIP(ip) {
    // Simple IP validation (IPv4 example)
    return /^(25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\.(\d{1,3}\.){2}\d{1,3}$/.test(
        ip
    );
}
