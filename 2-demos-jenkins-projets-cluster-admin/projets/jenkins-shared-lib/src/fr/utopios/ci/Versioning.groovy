package fr.utopios.ci

/** Helper de la Shared Library (repertoire src/) : calcul de version CI-friendly. */
class Versioning implements Serializable {
  static String fromBuild(int buildNumber, String base) {
    return "${base}.${buildNumber}"
  }
}
