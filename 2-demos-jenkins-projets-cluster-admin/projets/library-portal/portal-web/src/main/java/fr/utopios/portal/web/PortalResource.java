package fr.utopios.portal.web;

import fr.utopios.portal.LoanServiceBean;
import jakarta.ejb.EJB;
import jakarta.enterprise.context.RequestScoped;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.QueryParam;
import jakarta.ws.rs.core.MediaType;

@Path("/")
@RequestScoped
@Produces(MediaType.APPLICATION_JSON)
public class PortalResource {

    @EJB
    LoanServiceBean loans;

    /** Smoke test du deploiement (slide 9). */
    @GET
    @Path("health")
    public String health() {
        return "{\"status\":\"UP\"}";
    }

    @GET
    @Path("loans/check")
    public String check(@QueryParam("current") int current, @QueryParam("copies") int copies) {
        return "{\"canBorrow\":" + loans.canBorrow(current, copies) + "}";
    }
}
