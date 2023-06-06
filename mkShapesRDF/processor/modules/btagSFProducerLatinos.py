import ROOT
from mkShapesRDF.processor.framework.Module import Module
import correctionlib


correctionlib.register_pyroot_binding()


class btagSFProducerLatinos(Module):
    def __init__(self,
                 era, 
                 algo='deepJet', 
                 selectedWPs=['shape'], 
                 mode='shape',
                 pathToJson='',
                 jesSystsForShape=[]):


        super().__init__("btagSFProducerLatinos")
        self.era = era
        self.algo = algo
        self.selectedWPs = selectedWPs
        self.jesSystsForShape = jesSystsForShape
        self.mode = mode
        
        self.max_abs_eta = """2.49999"""
        self.min_pt = """20"""

        self.inputFileName = pathToJson
        self.measurement_types = None
        self.supported_wp = None

        self.systs = []
        self.central_and_systs = []
 
        self.systs_shape_corr = []
        self.central_and_systs_shape_corr = []
        

    def runModule(self, df, values):

        ### Correctionlib JSON structure
        supported_algos = {
            'deepCSV' : {
                'incl': {
                    'inputs' : ['systematic', 'working_point', 'flavor', 'abseta', 'pt'],
                    'systematic': ['central', 'down', 'down_correlated', 'down_uncorrelated', 'up', 'up_correlated', 'up_uncorrelated'],
                    'working_point' : ['L', 'M', 'T'],
                    'flavor' : {
                        'b' : 5,
                        'c' : 4,
                        'udsg' : 0
                    },
                    'abseta' : 'abs(Jet_eta)',
                    'pt' : 'Jet_pt'
                },
                'shape':{
                    'inputs' : ['systematic', 'working_point', 'flavor', 'abseta', 'pt'],
                    'systematic': ['hf', 'lf', 'hfstats1', 'hfstats2', 'lfstats1', 'lfstats2', 'cferr1', 'cferr2'],
                    'working_point' : ['L', 'M', 'T'],
                    'flavor' : {
                        'b' : 5,
                        'c' : 4,
                        'udsg' : 0
                    },
                    'abseta' : 'abs(Jet_eta)',
                    'pt' : 'Jet_pt',
                    'Discriminant' : 'Jet_btagDeepB'
                },
            },
            'deepJet' : {
                'incl': {
                    'inputs' : ['systematic', 'working_point', 'flavor', 'abseta', 'pt'],
                    'systematic': ['central', 'down', 'down_correlated', 'down_uncorrelated', 'up', 'up_correlated', 'up_uncorrelated'],
                    'working_point' : ['L', 'M', 'T'],
                    'flavor' : {
                        'b' : 5,
                        'c' : 4,
                        'udsg' : 0
                    },
                    'abseta' : 'abs(Jet_eta)',
                    'pt' : 'Jet_pt'
                },
                'shape':{
                    'inputs' : ['systematic', 'flavor', 'abseta', 'pt'],
                    'systematic': ['hf', 'lf', 'hfstats1', 'hfstats2', 'lfstats1', 'lfstats2', 'cferr1', 'cferr2'],
                    'flavor' : {
                        'b' : 5,
                        'c' : 4,
                        'udsg' : 0
                    },
                    'abseta' : 'abs(Jet_eta)',
                    'pt' : 'Jet_pt',
                    'Discriminant' : 'Jet_btagDeepFlavB'
                },
            }            
        }


        

        
        
        if self.algo not in supported_algos.keys():
            raise ValueError("ERROR: Algorithm '%s' not supported for era = '%s'! Please choose among { %s }." % (self.algo, self.era, supported_algos))

        if self.mode not in supported_algos[self.algo].keys():
            raise ValueError("ERROR: Algorithm '%s' not supported for mode = '%s'! Please choose among { %s }." % (self.algo, self.mode, supported_algos))

        if self.mode == 'incl':
            for wp in self.selectedWPs:
                if wp not in supported_algos[self.algo][self.mode]['working_point']:
                    raise ValueError("ERROR: Working point '%s' not supported for algo = '%s' and mode = '%s'! Please choose among { %s }." % (wp, self.algo, self.mode, self.supported_wp))

        
        branch_algo = {
            'deepCSV' : 'Jet_btagDeepB',
            'deepJet' : 'Jet_btagDeepFlavB'
        }
        branch_sfalgo = {
            'deepCSV' : 'deepcsv',
            'deepJet' : 'deepjet'
        }

        branch_name = branch_algo[self.algo]
        branch_sfname = branch_sfalgo[self.algo]

        # define systematic uncertainties
        self.systs = []
        self.systs.append("up")
        self.systs.append("down")
        self.central_and_systs = [ "central" ]
        self.central_and_systs.extend(self.systs)


        # define systs for shape SF
        self.systs_shape_corr = []
        for syst in [ 'lf', 'hf',
                      'hfstats1', 'hfstats2',
                      'lfstats1', 'lfstats2',
                      'cferr1', 'cferr2' ] + self.jesSystsForShape:
            self.systs_shape_corr.append("up_%s" % syst)
            self.systs_shape_corr.append("down_%s" % syst)
        self.central_and_systs_shape_corr = [ "central" ]
        self.central_and_systs_shape_corr.extend(self.systs_shape_corr)


        shape_syst = [ 'lf', 'hf',
                       'hfstats1', 'hfstats2',
                       'lfstats1', 'lfstats2',
                       'cferr1', 'cferr2' ] + self.jesSystsForShape
        


        #include "correction.h";

        ### Open Json                                                                                                                                                                                      
        ROOT.gInterpreter.Declare(
            f"""
            auto cset = correction::CorrectionSet::from_file("{self.inputFileName}");
            """
        )

        ROOT.gInterpreter.Declare(
            f"""
            auto cset_sf = cset->at("{self.algo}_{self.mode}");
            """
        )

        if self.mode == 'shape':
            
            ROOT.gInterpreter.Declare(
                """
                ROOT::RVecF getbtagSF_shape(std::string syst, ROOT::RVecI flav, ROOT::RVecF eta, ROOT::RVecF pt, ROOT::RVecF btag){
                    ROOT::RVecF sf(pt.size(), 1.0);
                    for (unsigned int i = 0, n = pt.size(); i < n; ++i) {
                            if (pt[i]<"""+self.min_pt+""" || abs(eta[i])>"""+self.max_abs_eta+"""){continue;}
                            if (syst.find("jes") != std::string::npos && flav[i]!=0){continue;}
                            if (syst.find("cferr") != std::string::npos){
                                    if (flav[i]==4){
                                            auto sf_tmp = cset_sf->evaluate({syst, flav[i], abs(eta[i]), pt[i], btag[i]});
                                            sf[i] = float(sf_tmp);
                                    }else{
                                        continue;
                                    }
                            }else if (syst.find("hf") != std::string::npos || syst.find("lf") != std::string::npos){
                                if (flav[i]==4){
                                        continue;
                                }else{
                                    auto sf_tmp = cset_sf->evaluate({syst, flav[i], abs(eta[i]), pt[i], btag[i]});
                                    sf[i] = float(sf_tmp);
                                }
                            }else{
                                auto sf_tmp = cset_sf->evaluate({syst, flav[i], abs(eta[i]), pt[i], btag[i]});
                                sf[i] = float(sf_tmp);
                            }
                    }
                    return sf;
                }
                """
            )
            
            for central_or_syst in self.central_and_systs_shape_corr:
                if central_or_syst=="central":
                    df = df.Define(
                        f'Jet_btagSF_{branch_sfname}_shape',
                        f'getbtagSF_shape("{central_or_syst}", abs(Jet_hadronFlavour), Jet_eta, Jet_pt, {branch_name})'
                    )
                else:
                    df = df.Define(
                        f'Jet_btagSF_{branch_sfname}_shape_{central_or_syst}',
                        f'getbtagSF_shape("{central_or_syst}", abs(Jet_hadronFlavour), Jet_eta, Jet_pt, {branch_name})'
                    )
            
            for syst in shape_syst:
                df = df.Vary(f'Jet_btagSF_{branch_sfname}_shape', "std::vector<ROOT::RVecF>{Jet_btagSF_"+branch_sfname+"_shape_up_"+syst+", Jet_btagSF_"+branch_sfname+"_shape_down_"+syst+"}", ["up", "down"], syst)
                df = df.DropColumns("Jet_btagSF_"+branch_sfname+"_shape_up_"+syst)
                df = df.DropColumns("Jet_btagSF_"+branch_sfname+"_shape_down_"+syst)

        else:

            ROOT.gInterpreter.Declare(
                """
                ROOT::RVecF getbtagSF_wp(std::string syst, std::string wp, ROOT::RVecI flav, ROOT::RVecF eta, ROOT::RVecF pt){
                    ROOT::RVecF sf(pt.size(), 1.0);
                    for (unsigned int i = 0, n = pt.size(); i < n; ++i) {
                            if (pt[i]<"""+self.min_pt+""" || abs(eta[i])>"""+self.max_abs_eta+"""){continue;}
                            auto sf_tmp = cset_sf->evaluate({syst, wp, flav[i], abs(eta[i]), pt[i]});
                            sf[i] = float(sf_tmp);
                    }
                    return sf;
                }
                """
            )
            
            for wp in self.selectedWPs:

                for central_or_syst in self.central_and_systs:
                    if central_or_syst=="central": 
                        df = df.Define(
                            f'Jet_btagSF_{branch_sfname}_{wp}',
                            f'getbtagSF_wp("{central_or_syst}", "{wp}", abs(Jet_hadronFlavour), Jet_eta, Jet_pt)'
                        )                    
                    else:
                        df = df.Define(
                            f'Jet_btagSF_{branch_sfname}_{wp}_{central_or_syst}',
                            f'getbtagSF_shape("{central_or_syst}", "{wp}", abs(Jet_hadronFlavour), Jet_eta, Jet_pt)'
                        )
                    
            for wp in self.selectedWPs:
                df = df.Vary(f'Jet_btagSF_{branch_sfname}_{wp}', "std::vector<ROOT::RVecF>{Jet_btagSF_"+branch_sfname+"_"+wp+"_up, Jet_btagSF_"+branch_sfname+"_"+wp+"_down}", ["up", "down"], f'Jet_btagSF_{branch_sfname}_{wp}_variation')
                df = df.DropColumns("Jet_btagSF_"+branch_sfname+"_"+wp+"_up")
                df = df.DropColumns("Jet_btagSF_"+branch_sfname+"_"+wp+"_down")
                

        return df
