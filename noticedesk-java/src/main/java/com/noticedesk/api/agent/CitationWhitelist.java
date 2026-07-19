package com.noticedesk.api.agent;

import java.util.Map;

public final class CitationWhitelist {

    public record CanonicalCase(String name, String canonicalUrl, String proposition) {}

    private static final Map<String, CanonicalCase> CANONICAL_CASES = Map.ofEntries(
        Map.entry("pushpam pharmaceuticals", new CanonicalCase(
            "Pushpam Pharmaceuticals Co. v. Collector of Central Excise, Bombay",
            "https://indiankanoon.org/doc/1690509/",
            "Suppression of facts under the proviso to s.11A Central Excise (now mirrored in s.74 CGST) requires deliberate withholding; mere non-disclosure is insufficient."
        )),
        Map.entry("cosmic dye chemical", new CanonicalCase(
            "Cosmic Dye Chemical v. Collector of Central Excise",
            "https://indiankanoon.org/doc/1623537/",
            "Extended period of limitation cannot be invoked without intent to evade tax; mens rea is essential."
        )),
        Map.entry("continental foundation", new CanonicalCase(
            "Continental Foundation Joint Venture v. CCE Chandigarh",
            "https://indiankanoon.org/doc/1107015/",
            "Suppression must be conscious and deliberate; a bona fide interpretation that is later disagreed with is not suppression."
        )),
        Map.entry("anand nishikawa", new CanonicalCase(
            "Anand Nishikawa Co. Ltd. v. Commissioner of Central Excise",
            "https://indiankanoon.org/doc/1257203/",
            "Suppression of facts in the proviso to s.11A is to be construed strictly; the department must show wilful misstatement."
        )),
        Map.entry("andaman timber", new CanonicalCase(
            "Andaman Timber Industries v. Commissioner of Central Excise",
            "https://indiankanoon.org/doc/24400737/",
            "Denial of cross-examination of witnesses whose statements are relied upon vitiates the adjudication order."
        )),
        Map.entry("suncraft energy", new CanonicalCase(
            "Suncraft Energy Pvt Ltd v. Assistant Commissioner, State Tax",
            "https://indiankanoon.org/doc/108089236/",
            "ITC cannot be denied to the recipient merely because the supplier failed to deposit tax."
        )),
        Map.entry("d.y. beathel", new CanonicalCase(
            "D.Y. Beathel Enterprises v. State Tax Officer",
            "https://indiankanoon.org/doc/108580056/",
            "Where supplier has not paid tax, reversal of ITC against the buyer without investigation of the supplier is unsustainable."
        )),
        Map.entry("on quest merchandising", new CanonicalCase(
            "On Quest Merchandising India Pvt Ltd v. Government of NCT of Delhi",
            "https://indiankanoon.org/doc/115886907/",
            "Section 9(2)(g) DVAT cannot deny ITC to a purchaser for the seller's default."
        )),
        Map.entry("bharti airtel", new CanonicalCase(
            "Commissioner of GST v. Bharti Airtel Ltd",
            "https://indiankanoon.org/doc/170611621/",
            "The Department bears the burden of establishing a demand on positive material; mere book entries or system mismatches do not discharge that burden."
        )),
        Map.entry("eicher motors", new CanonicalCase(
            "Eicher Motors Ltd v. Union of India",
            "https://indiankanoon.org/doc/1486002/",
            "Credit accrued is a vested right; subsequent legislation cannot retrospectively defeat it."
        )),
        Map.entry("larsen", new CanonicalCase(
            "Larsen & Toubro Ltd v. State of Karnataka",
            "https://indiankanoon.org/doc/89018960/",
            "Reconciliation between returns is a sufficient response where records bear out the assessee's position."
        )),
        Map.entry("amrit foods", new CanonicalCase(
            "Amrit Foods v. Commissioner of Central Excise, UP",
            "https://indiankanoon.org/doc/1379149/",
            "A show cause notice that does not specifically allege which limb of the proviso is invoked is bad in law."
        )),
        Map.entry("uniworth textiles", new CanonicalCase(
            "Uniworth Textiles Ltd v. CCE, Raipur",
            "https://indiankanoon.org/doc/164527889/",
            "Mere non-payment of tax is not equivalent to suppression; extended period requires positive act of suppression."
        )),
        Map.entry("ganga saran", new CanonicalCase(
            "ITO v. Ganga Saran & Sons (P) Ltd",
            "https://indiankanoon.org/doc/1521085/",
            "The 'reason to believe' for s.148 reopening must have a rational connection with the material on record."
        )),
        Map.entry("kelvinator", new CanonicalCase(
            "CIT v. Kelvinator of India Ltd",
            "https://indiankanoon.org/doc/1192802/",
            "Reassessment under s.148 cannot be based on a mere change of opinion; tangible material is required."
        )),
        Map.entry("ashish agarwal", new CanonicalCase(
            "Union of India v. Ashish Agarwal",
            "https://indiankanoon.org/doc/183568974/",
            "Section 148A(b) procedure must be followed for reassessment notices issued under the new regime."
        ))
    );

    private CitationWhitelist() {}

    public static CanonicalCase lookupCanonical(String caseName) {
        String needle = caseName.toLowerCase();
        for (Map.Entry<String, CanonicalCase> entry : CANONICAL_CASES.entrySet()) {
            if (needle.contains(entry.getKey())) {
                return entry.getValue();
            }
        }
        return null;
    }
}
