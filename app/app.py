from flask import (
    Flask,
    render_template,
    url_for,
    request,
    redirect,
    session,
    flash,
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from werkzeug.security import generate_password_hash, check_password_hash
import os


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
db.init_app(app)
app.secret_key = "wanny123"


class Equipement(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(nullable=False)
    type_equipement: Mapped[str]
    marque: Mapped[str]
    adresse_ip: Mapped[str] = mapped_column(nullable=True)
    localisation: Mapped[str]
    statut: Mapped[str]


class Utilisateur(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(nullable=False, unique=True)
    mot_de_passe: Mapped[str] = mapped_column(nullable=False)
    est_admin: Mapped[bool] = mapped_column(default=False)


with app.app_context():
    db.create_all()


@app.route("/")
def inscription():
    return render_template("inscription.html")


@app.route("/connexion")
def connexion():
    return render_template("connexion.html")


@app.route("/nouvel_utilisateur", methods=["post", "get"])
def nouvel_utilisateur():
    if request.method == "POST":
        donnee = request.form
        password_hache = generate_password_hash(donnee.get("password"))
        utilisateur = Utilisateur(
            nom=donnee.get("nom"),
            email=donnee.get("email"),
            mot_de_passe=password_hache,
        )
        db.session.add(utilisateur)
        try:
            db.session.commit()
            flash("Utilisateur enregistré avec succès !", "success")
            return redirect(url_for("login"))

        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors de l'enregistrement : {e}", "danger")
            return render_template("inscription.html")
    else:
        return render_template("inscription.html")


@app.route("/login", methods=["get", "post"])
def login():
    if request.method == "POST":
        # 1. Récupérer les données du formulaire
        nom_saisi = request.form.get("nom")
        password_saisi = request.form.get("password")

        # 2. Chercher l'utilisateur dans la base de données
        # On utilise .filter_by() pour trouver le nom exact
        utilisateur_saisi = db.session.execute(
            db.select(Utilisateur).filter_by(nom=nom_saisi)
        ).scalar()

        # 3. Vérification
        if utilisateur_saisi and check_password_hash(
            utilisateur_saisi.mot_de_passe, password_saisi
        ):
            session["utilisateur_id"] = utilisateur_saisi.id
            session["nom"] = utilisateur_saisi.nom
            session["est_admin"] = utilisateur_saisi.est_admin
            # Succès : Le hash correspond au mot de passe en clair
            flash(f"Connexion réussie pour {nom_saisi}", "success"),
            flash(f"Session créée pour l'ID {utilisateur_saisi.id}", "success")
            return redirect(url_for("accueil"))
        else:
            # Échec : Utilisateur inconnu ou mauvais mot de passe
            flash("Échec de la connexion", "danger")
            return render_template("connexion.html")

    # Si c'est un GET, on affiche juste la page de login
    return render_template("connexion.html")


@app.route("/accueil")
def accueil():
    # 1. Vérification de la session
    if "utilisateur_id" not in session:
        return redirect(url_for("login"))
    else:
        # 2. Récupération des données (Application des filtres AVANT execute)
        # Pour le total
        nbr_total = len(
            db.session.execute(db.select(Equipement)).scalars().all()
        )

        # Filtrage par statut
        nbr_en_marche = len(
            db.session.execute(
                db.select(Equipement).filter_by(statut="En marche")
            )
            .scalars()
            .all()
        )
        nbr_a_arret = len(
            db.session.execute(
                db.select(Equipement).filter_by(statut="A l'arrêt")
            )
            .scalars()
            .all()
        )

        # Filtrage par type d'équipement
        nbr_switch = len(
            db.session.execute(
                db.select(Equipement).filter_by(type_equipement="Switch")
            )
            .scalars()
            .all()
        )
        nbr_routeur = len(
            db.session.execute(
                db.select(Equipement).filter_by(type_equipement="Routeur")
            )
            .scalars()
            .all()
        )
        nbr_PC = len(
            db.session.execute(
                db.select(Equipement).filter_by(type_equipement="PC")
            )
            .scalars()
            .all()
        )
        nbr_imprimante = len(
            db.session.execute(
                db.select(Equipement).filter_by(type_equipement="Imprimantes")
            )
            .scalars()
            .all()
        )
        nbr_telephone = len(
            db.session.execute(
                db.select(Equipement).filter_by(type_equipement="Téléphones")
            )
            .scalars()
            .all()
        )

        # 3. Envoi au template
        return render_template(
            "accueil.html",
            nom=session.get("nom"),
            nbr_total=nbr_total,
            nbr_en_marche=nbr_en_marche,
            nbr_a_arret=nbr_a_arret,
            nbr_switch=nbr_switch,
            nbr_routeur=nbr_routeur,
            nbr_PC=nbr_PC,
            nbr_imprimante=nbr_imprimante,
            nbr_telephone=nbr_telephone,
        )


@app.route("/deconnexion")
def deconnexion():
    session.clear()  # Supprime toutes les données de session
    return redirect(url_for("login"))


@app.route("/inventaire")
def inventaire():
    if "utilisateur_id" not in session:
        # Si non, on renvoie vers le login
        return redirect(url_for("login"))
    filtre_type_equipement = request.args.get("filtre_type_equipement")
    filtre_marque = request.args.get("filtre_marque")
    filtre_localisation = request.args.get("filtre_localisation")
    filtre_statut = request.args.get("filtre_statut")
    requete = db.select(Equipement)

    if filtre_type_equipement:
        requete = requete.filter_by(type_equipement=filtre_type_equipement)
    if filtre_marque:
        requete = requete.filter_by(marque=filtre_marque)
    if filtre_localisation:
        requete = requete.filter_by(localisation=filtre_localisation)
    if filtre_statut:
        requete = requete.filter_by(statut=filtre_statut)
    equipements = db.session.execute(requete).scalars().all()

    return render_template(
        "inventaire.html",
        equipements=equipements,
        filtre_type_equipement=filtre_type_equipement,
        filtre_marque=filtre_marque,
        filtre_localisation=filtre_localisation,
        filtre_statut=filtre_statut,
    )


@app.route("/admin/ajouter", methods=["get", "post"])
def ajouter():
    if "utilisateur_id" not in session:
        return redirect(url_for("login"))
    else:
        if session["est_admin"] is True:
            if request.method == "GET":
                return render_template(
                    "ajouter.html", action="/admin/ajouter", bouton="Ajouter"
                )
            else:
                données = request.form
                nouvel_equipement = Equipement(
                    nom=données.get("nom"),
                    type_equipement=données.get("type_equipement"),
                    marque=données.get("marque"),
                    adresse_ip=données.get("adresse_ip"),
                    localisation=données.get("localisation"),
                    statut=données.get("statut"),
                )
                db.session.add(nouvel_equipement)
                try:
                    db.session.commit()
                    print("Equipement enregistré avec succès !")
                    return redirect(url_for("inventaire"))
                except Exception as e:
                    db.session.rollback()
                    flash(f"Erreur lors de l'enregistrement : {e}", "danger")
                    return render_template("ajouter.html")
        else:
            return redirect(url_for("accueil"))


@app.route("/admin/modifier/<int:id>", methods=["get", "post"])
def modifier(id):
    if "utilisateur_id" not in session:
        return redirect(url_for("login"))
    else:
        if session["est_admin"] is True:
            equipement_a_modifier = db.session.get(Equipement, id)
            if not equipement_a_modifier:
                flash(
                    f"Erreur : L'équipement ID {id} est introuvable.", "danger"
                )
                return redirect(url_for("accueil"))
            else:
                if request.method == "GET":
                    return render_template(
                        "ajouter.html",
                        equipement=equipement_a_modifier,
                        action=f"/admin/modifier/{id}",
                        bouton="Modifier",
                    )
                else:
                    equipement_a_modifier.nom = request.form.get("nom")
                    equipement_a_modifier.type_equipement = request.form.get(
                        "type_equipement"
                    )
                    equipement_a_modifier.marque = request.form.get("marque")
                    equipement_a_modifier.adresse_ip = request.form.get(
                        "adresse_ip"
                    )
                    equipement_a_modifier.localisation = request.form.get(
                        "localisation"
                    )
                    equipement_a_modifier.statut = request.form.get("statut")
                    try:
                        db.session.commit()
                        print("Equipement modifié avec succès !")
                        return redirect(url_for("inventaire"))
                    except Exception as e:
                        db.session.rollback()
                        flash(
                            f"Erreur lors de la modification : {e}",
                            "danger",
                        )
                        return render_template("ajouter.html")


@app.route("/admin/supprimer/<int:id>", methods=["post"])
def supprimer(id):
    if "utilisateur_id" not in session:
        return redirect(url_for("login"))
    else:
        if session["est_admin"] is True:
            equipement_a_supprimer = db.session.get(Equipement, id)
            if not equipement_a_supprimer:
                flash(
                    f"Erreur : L'équipement ID {id} est introuvable.",
                    "danger",
                )
                return redirect(url_for("accueil"))
            else:
                db.session.delete(equipement_a_supprimer)
                db.session.commit()
                return redirect(url_for("inventaire"))


@app.route("/carte")
def carte():
    if "utilisateur_id" not in session:
        return redirect(url_for("login"))
    else:
        nbr_en_H0_05 = len(
            db.session.execute(
                db.select(Equipement).filter_by(localisation="H0-05")
            )
            .scalars()
            .all()
        )
        nbr_en_H1_11 = len(
            db.session.execute(
                db.select(Equipement).filter_by(localisation="H1-11")
            )
            .scalars()
            .all()
        )
        nbr_en_J0_01 = len(
            db.session.execute(
                db.select(Equipement).filter_by(localisation="J0-01")
            )
            .scalars()
            .all()
        )
        nbr_en_J0_09 = len(
            db.session.execute(
                db.select(Equipement).filter_by(localisation="J0-09")
            )
            .scalars()
            .all()
        )
        nbr_en_J0_04 = len(
            db.session.execute(
                db.select(Equipement).filter_by(localisation="J0-04")
            )
            .scalars()
            .all()
        )
        nbr_en_I0_02 = len(
            db.session.execute(
                db.select(Equipement).filter_by(localisation="I0-02")
            )
            .scalars()
            .all()
        )
        nbr_en_Reserve = len(
            db.session.execute(
                db.select(Equipement).filter_by(localisation="Réserve")
            )
            .scalars()
            .all()
        )
        return render_template(
            "carte.html",
            nbr_en_H0_05=nbr_en_H0_05,
            nbr_en_H1_11=nbr_en_H1_11,
            nbr_en_J0_01=nbr_en_J0_01,
            nbr_en_J0_09=nbr_en_J0_09,
            nbr_en_J0_04=nbr_en_J0_04,
            nbr_en_I0_02=nbr_en_I0_02,
            nbr_en_Reserve=nbr_en_Reserve,
        )


if __name__ == "__main__":
    # TRÈS IMPORTANT : host='0.0.0.0' permet à Docker d'exposer le site
    app.run(host="0.0.0.0", port=5000, debug=True)
