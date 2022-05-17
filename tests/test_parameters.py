"""
Run tests on individual parameters.
"""

import sciris as sc
import fpsim as fp

do_plot = True
sc.options(backend='agg') # Turn off interactive plots


def test_null(do_plot=do_plot):
    sc.heading('Testing no births, no deaths...')

    pars = fp.pars('test') # For default pars
    pars['age_mortality']['f'] *= 0
    pars['age_mortality']['m'] *= 0
    pars['age_mortality']['trend'] *= 0
    pars['maternal_mortality']['probs'] *= 0
    pars['infant_mortality']['probs'] *= 0
    pars['exposure_correction'] = 0
    pars['high_parity']         = 4
    pars['high_parity_nonuse_correction']  = 0

    sim = fp.Sim(pars)
    sim.run()

    if do_plot:
        sim.plot()

    return sim


def test_method_timestep():
    sc.heading('Test sim speed')

    pars1 = fp.pars(location='test', method_timestep=1)
    pars2 = fp.pars(location='test', method_timestep=6)
    sim1 = fp.Sim(pars1)
    sim2 = fp.Sim(pars2)

    T = sc.timer()

    sim1.run()
    t1 = T.tt(output=True)

    sim2.run()
    t2 = T.tt(output=True)

    assert t2 < t1, 'Expecting runtime to be less with a larger method timestep'

    return [t1, t2]


def test_mcpr_growth():
    sc.heading('Test MCPR growth assumptions')

    pars = dict(
        start_year = 2010,
        end_year   = 2030, # Should be after last MCPR data year
    )

    pars1 = fp.pars(location='test', mcpr_growth_rate=-0.05, **pars)
    pars2 = fp.pars(location='test', mcpr_growth_rate=0.05, **pars)
    sim1 = fp.Sim(pars1)
    sim2 = fp.Sim(pars2)

    msim = fp.MultiSim([sim1, sim2]).run()
    s1 = msim.sims[0]
    s2 = msim.sims[1]

    mcpr_last = pars1['methods']['mcpr_rates'][-1] # Last MCPR data point
    decreasing = s1.results['mcpr'][-1]
    increasing = s2.results['mcpr'][-1]

    assert mcpr_last > decreasing, f'Negative MCPR growth did not reduce MCPR ({decreasing} ≥ {mcpr_last})'
    assert mcpr_last < increasing, f'Positive MCPR growth did not increase MCPR ({increasing} ≤ {mcpr_last})'

    return [s1, s2]



if __name__ == '__main__':

    sc.options(backend=None) # Turn on interactive plots
    with sc.timer():
        null = test_null(do_plot=do_plot)
        timings = test_method_timestep()
        sims = test_mcpr_growth()
