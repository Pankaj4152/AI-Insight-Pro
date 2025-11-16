from flask import Flask, jsonify, request
from flask_cors import CORS # Add this line to import CORS
from db_connection import get_db_connection
from regulation_sdes import REGULATION_SDEs # Import the full dictionary

app = Flask(__name__)
CORS(app) # Add this line to enable CORS for all routes

# Table names from your database schema
CLIENT_SDE_TABLE = "client_selected_sdes"
OUTPUT_TABLE = "compliance_scores"

@app.route('/calculate_compliance', methods=['POST'])
def calculate_compliance():
    data = request.get_json()
    client_id = data.get('client_id')

    if not client_id:
        return jsonify({"error": "client_id is required"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cursor = conn.cursor()
        
        # 1. Fetch client's selected SDEs
        query_sdes = f"SELECT pattern_name FROM {CLIENT_SDE_TABLE} WHERE client_id = %s"
        cursor.execute(query_sdes, (client_id,))
        client_sdes_results = cursor.fetchall()
        client_selected_sdes = {row[0] for row in client_sdes_results}
        
        if not client_selected_sdes:
            return jsonify({"error": f"No SDEs found for client with ID {client_id}."}), 404

        # 2. Find the best-fit regulation based on SDE matches
        best_match_count = -1
        best_fit_regulation = None
        best_fit_required_sdes = []

        for reg_name, details in REGULATION_SDEs.items():
            required_sdes_set = set(details["required_sdes"])
            matched_sdes = client_selected_sdes.intersection(required_sdes_set)
            match_count = len(matched_sdes)

            if match_count > best_match_count:
                best_match_count = match_count
                best_fit_regulation = reg_name
                best_fit_required_sdes = required_sdes_set
        
        if not best_fit_regulation:
            return jsonify({"error": "Could not determine a suitable regulation."}), 500

        # 3. Calculate Compliance %
        total_required = len(best_fit_required_sdes)
        score = (best_match_count / total_required) * 100 if total_required > 0 else 0
        
        # 4. Determine compliance status
        if score >= 80:
            status = "Highly Compliant"
        elif 50 <= score < 80:
            status = "Partially Compliant"
        else:
            status = "Low Compliance"

        # 5. List missing SDEs
        missing_sdes = best_fit_required_sdes - client_selected_sdes

        # 6. Generate output object
        output = {
            "client_id": client_id,
            "inferred_regulation": best_fit_regulation,
            "total_required": total_required,
            "matched": best_match_count,
            "score": round(score, 2),
            "status": status,
            "missing_sdes": list(missing_sdes),
            "recommendation": f"Based on your data, the most applicable regulation is {best_fit_regulation}. To be more compliant, consider adding the following SDEs: {', '.join(list(missing_sdes))}."
        }
        
        # 7. Save output to the new table
        save_query = f"""
            INSERT INTO {OUTPUT_TABLE} (client_id, inferred_regulation, total_required, matched, score, status, recommendation)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (client_id) DO UPDATE
            SET inferred_regulation = EXCLUDED.inferred_regulation,
                total_required = EXCLUDED.total_required,
                matched = EXCLUDED.matched,
                score = EXCLUDED.score,
                status = EXCLUDED.status,
                recommendation = EXCLUDED.recommendation;
        """
        cursor.execute(save_query, (
            output['client_id'],
            output['inferred_regulation'],
            output['total_required'],
            output['matched'],
            output['score'],
            output['status'],
            output['recommendation']
        ))
        conn.commit()

        return jsonify(output)

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
